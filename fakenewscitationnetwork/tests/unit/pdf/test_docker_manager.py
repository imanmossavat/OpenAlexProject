import pytest
from unittest.mock import Mock, patch
import subprocess
import requests
from ArticleCrawler.pdf_processing.docker_manager import DockerManager


@pytest.mark.unit
class TestDockerManager:
    
    @pytest.fixture
    def docker_manager(self, mock_logger):
        return DockerManager(logger=mock_logger)
    
    def test_initialization_default(self, mock_logger):
        manager = DockerManager(logger=mock_logger)
        assert manager.image == "lfoppiano/grobid:0.8.2"
        assert manager.port == 8070
        assert manager.base_url == "http://localhost:8070"
    
    def test_initialization_custom(self, mock_logger):
        manager = DockerManager(image="custom/grobid:1.0", port=9000, logger=mock_logger)
        assert manager.image == "custom/grobid:1.0"
        assert manager.port == 9000
        assert manager.base_url == "http://localhost:9000"
    
    @patch('subprocess.run')
    def test_is_docker_available_success(self, mock_run, docker_manager):
        mock_run.return_value = Mock(returncode=0)
        assert docker_manager.is_docker_available() is True
    
    @patch('subprocess.run')
    def test_is_docker_available_not_installed(self, mock_run, docker_manager):
        mock_run.side_effect = FileNotFoundError()
        assert docker_manager.is_docker_available() is False
    
    @patch('subprocess.run')
    def test_is_docker_available_timeout(self, mock_run, docker_manager):
        mock_run.side_effect = subprocess.TimeoutExpired('docker', 5)
        assert docker_manager.is_docker_available() is False
    
    @patch('requests.get')
    def test_is_grobid_running_success(self, mock_get, docker_manager):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        assert docker_manager.is_grobid_running() is True
        mock_get.assert_called_once_with("http://localhost:8070/api/isalive", timeout=5)
    
    @patch('requests.get')
    def test_is_grobid_running_not_available(self, mock_get, docker_manager):
        mock_get.side_effect = requests.RequestException()
        assert docker_manager.is_grobid_running() is False
    
    @patch('subprocess.run')
    def test_is_container_running_true(self, mock_run, docker_manager):
        mock_run.return_value = Mock(stdout="grobid-service\n", returncode=0)
        assert docker_manager.is_container_running() is True
    
    @patch('subprocess.run')
    def test_is_container_running_false(self, mock_run, docker_manager):
        mock_run.return_value = Mock(stdout="", returncode=0)
        assert docker_manager.is_container_running() is False
    
    @patch.object(DockerManager, 'is_docker_available')
    @patch.object(DockerManager, 'is_container_running')
    @patch('subprocess.run')
    @patch.object(DockerManager, '_wait_for_ready')
    def test_start_container_success(self, mock_wait, mock_run, mock_is_running, mock_docker_available, docker_manager, mock_logger):
        mock_docker_available.return_value = True
        mock_is_running.return_value = False
        mock_run.return_value = Mock(returncode=0)
        mock_wait.return_value = True
        result = docker_manager.start_container()
        assert result is True
        mock_logger.info.assert_called()
    
    @patch.object(DockerManager, 'is_docker_available')
    def test_start_container_docker_not_available(self, mock_docker_available, docker_manager, mock_logger):
        mock_docker_available.return_value = False
        result = docker_manager.start_container()
        assert result is False
        mock_logger.error.assert_called()
    
    @patch.object(DockerManager, 'is_docker_available')
    @patch.object(DockerManager, 'is_container_running')
    def test_start_container_already_running(self, mock_is_running, mock_docker_available, docker_manager, mock_logger):
        mock_docker_available.return_value = True
        mock_is_running.return_value = True
        result = docker_manager.start_container()
        assert result is True
        mock_logger.info.assert_called()
    
    @patch.object(DockerManager, 'is_grobid_running')
    @patch('time.sleep')
    def test_wait_for_ready_success(self, mock_sleep, mock_is_running, docker_manager):
        mock_is_running.side_effect = [False, False, True]
        result = docker_manager._wait_for_ready(timeout=10, check_interval=2)
        assert result is True
    
    @patch.object(DockerManager, 'is_grobid_running')
    @patch('time.sleep')
    def test_wait_for_ready_timeout(self, mock_sleep, mock_is_running, docker_manager, mock_logger):
        mock_is_running.return_value = False
        result = docker_manager._wait_for_ready(timeout=1, check_interval=1)
        assert result is False
        mock_logger.error.assert_called()
    
    @patch.object(DockerManager, 'is_container_running')
    def test_stop_container_not_running(self, mock_is_running, docker_manager):
        mock_is_running.return_value = False
        result = docker_manager.stop_container()
        assert result is True
    
    @patch.object(DockerManager, 'is_container_running')
    @patch('subprocess.run')
    def test_stop_container_success(self, mock_run, mock_is_running, docker_manager, mock_logger):
        mock_is_running.return_value = True
        mock_run.return_value = Mock(returncode=0)
        result = docker_manager.stop_container()
        assert result is True
        mock_logger.info.assert_called()
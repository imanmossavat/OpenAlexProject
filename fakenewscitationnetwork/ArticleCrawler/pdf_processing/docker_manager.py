
import logging
import os
import subprocess
import time
from typing import Optional

import requests


class DockerManager:
    DEFAULT_IMAGE = "lfoppiano/grobid:0.8.2"
    DEFAULT_PORT = 8070
    CONTAINER_NAME = "grobid-service"
    
    def __init__(
        self,
        image: str = DEFAULT_IMAGE,
        port: int = DEFAULT_PORT,
        logger: Optional[logging.Logger] = None,
        base_url: Optional[str] = None,
    ):
        self.image = image
        self.port = port
        self.logger = logger or logging.getLogger(__name__)
        env_url = os.getenv("GROBID_URL") or os.getenv("GROBID_BASE_URL")
        self.base_url = base_url or env_url or f"http://localhost:{port}"
    
    def is_docker_available(self) -> bool:
        try:
            result = subprocess.run(
                ["docker", "version"],
                capture_output=True,
                timeout=1
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def is_grobid_running(self) -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/api/isalive",
                timeout=1
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def is_container_running(self) -> bool:
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={self.CONTAINER_NAME}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=1
            )
            return self.CONTAINER_NAME in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def start_container(self, wait_for_ready: bool = True) -> bool:
        if not self.is_docker_available():
            self.logger.error("Docker is not available")
            return False
        
        if self.is_grobid_running():
            self.logger.info("GROBID is already running")
            return True
        
        self._stop_existing_container()
        
        try:
            self.logger.info(f"Starting GROBID container on port {self.port}...")
            
            subprocess.run(
                [
                    "docker", "run",
                    "-d",
                    "--name", self.CONTAINER_NAME,
                    "-p", f"{self.port}:8070",
                    "--rm",
                    self.image
                ],
                capture_output=True,
                check=True,
                timeout=30
            )
            
            if wait_for_ready:
                return self._wait_for_ready()
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to start container: {e.stderr.decode()}")
            return False
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout starting container")
            return False
    
    def _stop_existing_container(self):
        try:
            subprocess.run(
                ["docker", "stop", self.CONTAINER_NAME],
                capture_output=True,
                timeout=10
            )
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass
    
    def _wait_for_ready(self, timeout: int = 60, check_interval: int = 2) -> bool:
        self.logger.info("Waiting for GROBID service to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_grobid_running():
                self.logger.info("GROBID service is ready")
                return True
            
            time.sleep(check_interval)
        
        self.logger.error(f"GROBID service did not become ready within {timeout} seconds")
        return False
    
    def stop_container(self) -> bool:
        if not self.is_container_running():
            return True
        
        try:
            self.logger.info("Stopping GROBID container...")
            subprocess.run(
                ["docker", "stop", self.CONTAINER_NAME],
                capture_output=True,
                check=True,
                timeout=30
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            self.logger.error(f"Failed to stop container: {e}")
            return False

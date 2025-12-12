import { useCallback, useEffect, useState } from 'react'

import apiClient from '@/shared/api/client'
import { endpoints } from '@/shared/api/endpoints'

import { DEFAULT_GROBID_STATUS } from '../constants'

export default function usePdfImport({ sessionId, navigate, onSuccess }) {
  const [showPdfModal, setShowPdfModal] = useState(false)
  const [pdfFiles, setPdfFiles] = useState([])
  const [pdfLoading, setPdfLoading] = useState(false)
  const [pdfError, setPdfError] = useState(null)
  const [grobidStatus, setGrobidStatus] = useState(DEFAULT_GROBID_STATUS)

  useEffect(() => {
    if (!showPdfModal || !sessionId) return
    let isCancelled = false
    setGrobidStatus(DEFAULT_GROBID_STATUS)
    const checkGrobid = async () => {
      const res = await apiClient('GET', `${endpoints.seedsSession}/${sessionId}/pdfs/grobid/status`)
      if (isCancelled) return
      if (res.error) {
        setGrobidStatus({ checked: true, available: false, message: res.error })
        return
      }
      const available = Boolean(res.data?.available)
      setGrobidStatus({
        checked: true,
        available,
        message:
          res.data?.message ||
          (available
            ? null
            : 'GROBID service is not running. Please start it before uploading PDF files.'),
      })
    }
    checkGrobid()
    return () => {
      isCancelled = true
    }
  }, [showPdfModal, sessionId])

  const openPdfModal = useCallback(() => {
    setShowPdfModal(true)
    setPdfError(null)
  }, [])

  const closePdfModal = useCallback(() => {
    setShowPdfModal(false)
    setPdfFiles([])
    setPdfError(null)
    setGrobidStatus(DEFAULT_GROBID_STATUS)
  }, [])

  const confirmPdfUpload = useCallback(async () => {
    if (!sessionId || !pdfFiles.length) {
      setPdfError('Select at least one PDF file')
      return
    }
    setPdfLoading(true)
    setPdfError(null)
    try {
      const uploadForm = new FormData()
      pdfFiles.forEach((file) => uploadForm.append('files', file))
      const upload = await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/pdfs/upload`, uploadForm)
      if (upload.error) throw new Error(upload.error)
      const uploadId = upload.data?.upload_id
      if (!uploadId) throw new Error('Upload failed to return upload_id')
      const extract = await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/pdfs/${uploadId}/extract`)
      if (extract.error) throw new Error(extract.error)
      const reviews = (extract.data?.results || []).map((result) => ({
        filename: result.filename,
        action: result.success ? 'accept' : 'skip',
        edited_metadata: result.metadata,
      }))
      const reviewRes = await apiClient(
        'POST',
        `${endpoints.seedsSession}/${sessionId}/pdfs/${uploadId}/review`,
        { reviews }
      )
      if (reviewRes.error) throw new Error(reviewRes.error)
      const stage = await apiClient('POST', `${endpoints.seedsSession}/${sessionId}/pdfs/${uploadId}/stage`)
      if (stage.error) throw new Error(stage.error)
      closePdfModal()
      onSuccess?.()
    } catch (err) {
      setPdfError(err.message || 'Failed to import PDFs')
    }
    setPdfLoading(false)
  }, [sessionId, pdfFiles, closePdfModal, onSuccess])

  return {
    showPdfModal,
    openPdfModal,
    closePdfModal,
    pdfFiles,
    setPdfFiles,
    pdfLoading,
    pdfError,
    grobidStatus,
    setPdfError,
    confirmPdfUpload,
    navigateToGrobidHelp: () => navigate('/help/grobid'),
  }
}

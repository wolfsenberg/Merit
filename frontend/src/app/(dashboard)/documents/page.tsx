"use client";

import { useState, useCallback } from "react";
import { useUploadDocument } from "@/hooks/use-api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const ACCEPTED_TYPES = ["image/png", "image/jpeg", "image/webp", "application/pdf"];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export default function DocumentsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState("grade_slip");
  const [submissionId, setSubmissionId] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [validationError, setValidationError] = useState("");

  const uploadDocument = useUploadDocument();

  const validateFile = (f: File): boolean => {
    setValidationError("");
    if (!ACCEPTED_TYPES.includes(f.type)) {
      setValidationError("Invalid file type. Please upload PNG, JPEG, WebP, or PDF.");
      return false;
    }
    if (f.size > MAX_FILE_SIZE) {
      setValidationError("File too large. Maximum size is 10MB.");
      return false;
    }
    return true;
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (validateFile(droppedFile)) {
        setFile(droppedFile);
      }
    }
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      if (validateFile(selectedFile)) {
        setFile(selectedFile);
      }
    }
  };

  const handleUpload = async () => {
    if (!file || !submissionId) return;
    await uploadDocument.mutateAsync({ file, documentType, submissionId });
    setFile(null);
    setSubmissionId("");
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">Document Upload</h1>

      <Card>
        <CardHeader>
          <CardTitle>Upload Document</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Drag and Drop Area */}
          <div
            className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
              dragActive
                ? "border-gold-500 bg-gold-50"
                : "border-gray-300 hover:border-gray-400"
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {file ? (
              <div className="text-center">
                <p className="font-medium">{file.name}</p>
                <p className="text-sm text-muted-foreground">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={() => setFile(null)}
                >
                  Remove
                </Button>
              </div>
            ) : (
              <div className="text-center">
                <p className="mb-2 text-sm text-muted-foreground">
                  Drag & drop a file here, or click to browse
                </p>
                <p className="text-xs text-muted-foreground">
                  PNG, JPEG, WebP, or PDF (max 10MB)
                </p>
                <Input
                  type="file"
                  accept=".png,.jpg,.jpeg,.webp,.pdf"
                  onChange={handleFileInput}
                  className="mt-3 w-auto"
                />
              </div>
            )}
          </div>

          {validationError && (
            <p className="text-sm text-red-600">{validationError}</p>
          )}

          {/* Document Type */}
          <div>
            <Label htmlFor="doc-type">Document Type</Label>
            <select
              id="doc-type"
              className="w-full rounded border px-3 py-2 text-sm"
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
            >
              <option value="grade_slip">Grade Slip</option>
              <option value="enrollment_form">Enrollment Form</option>
              <option value="certificate">Certificate</option>
              <option value="transcript">Transcript</option>
              <option value="id_document">ID Document</option>
              <option value="report">Report</option>
              <option value="custom">Custom</option>
            </select>
          </div>

          {/* Submission ID */}
          <div>
            <Label htmlFor="submission-id">Submission ID</Label>
            <Input
              id="submission-id"
              value={submissionId}
              onChange={(e) => setSubmissionId(e.target.value)}
              placeholder="Enter your submission ID"
            />
          </div>

          {uploadDocument.error && (
            <p className="text-sm text-red-600">Upload failed. Please try again.</p>
          )}

          {uploadDocument.isSuccess && (
            <p className="text-sm text-green-600">Document uploaded successfully!</p>
          )}

          <Button
            className="w-full"
            onClick={handleUpload}
            disabled={!file || !submissionId || uploadDocument.isPending}
          >
            {uploadDocument.isPending ? "Uploading..." : "Upload Document"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

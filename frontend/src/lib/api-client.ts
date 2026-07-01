"use client";

import { authFetch, type AuthUser, type TokenPair } from "./auth";

/**
 * Typed API client for Merit Platform.
 * Uses authFetch for automatic JWT attachment and 401 auto-refresh.
 */

// ─── Base URL ────────────────────────────────────────────────────────────────

const API_BASE = "/api/v1";

// ─── Error Handling ──────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body?: unknown
  ) {
    super(`API Error ${status}: ${statusText}`);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      body = undefined;
    }
    throw new ApiError(response.status, response.statusText, body);
  }
  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

// ─── Request Helpers ─────────────────────────────────────────────────────────

async function get<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== "") {
        url.searchParams.set(key, value);
      }
    });
  }
  const response = await authFetch(url.toString());
  return handleResponse<T>(response);
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const response = await authFetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return handleResponse<T>(response);
}

async function put<T>(path: string, body?: unknown): Promise<T> {
  const response = await authFetch(`${API_BASE}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return handleResponse<T>(response);
}

async function uploadFile<T>(path: string, file: File, fields?: Record<string, string>): Promise<T> {
  const formData = new FormData();
  formData.append("file", file);
  if (fields) {
    Object.entries(fields).forEach(([key, value]) => {
      formData.append(key, value);
    });
  }
  const response = await authFetch(`${API_BASE}${path}`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<T>(response);
}

// ─── Response Types ──────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  cursor?: string;
  has_more: boolean;
}

export interface Program {
  id: string;
  organization_id: string;
  name: string;
  description: string;
  status: "draft" | "active" | "paused" | "completed" | "archived";
  funding_amount_per_recipient: number;
  max_recipients: number;
  current_recipients: number;
  total_funded: number;
  start_date: string;
  end_date?: string;
  created_at: string;
  updated_at: string;
}

export interface ProgramRequirement {
  id: string;
  program_id: string;
  requirement_type: string;
  description: string;
  condition_operator: string;
  condition_value: string;
  is_mandatory: boolean;
  verification_frequency: string;
}

export interface Application {
  id: string;
  program_id: string;
  recipient_id: string;
  status: string;
  submitted_at: string;
}

export interface Document {
  id: string;
  submission_id: string;
  file_name: string;
  file_type: string;
  document_type: string;
  status: string;
  uploaded_at: string;
}

export interface OcrResult {
  document_id: string;
  extracted_text: string;
  structured_data: Record<string, unknown>;
  confidence_score: number;
  processing_time_ms: number;
}

export interface ComplianceEvaluation {
  id: string;
  recipient_id: string;
  program_id: string;
  overall_status: "eligible" | "ineligible" | "pending_verification" | "partial";
  rule_results: RuleResult[];
  evaluated_at: string;
  next_evaluation_due?: string;
}

export interface RuleResult {
  requirement_id: string;
  requirement_type: string;
  condition: string;
  actual_value?: string;
  expected_value: string;
  passed: boolean;
  reason: string;
}

export interface WalletInfo {
  id: string;
  user_id: string;
  public_key: string;
  balance: number;
  network: string;
  created_at: string;
}

export interface CashOutRequest {
  amount: number;
  method: string;
  account_number: string;
  account_name: string;
}

export interface CashOutResponse {
  id: string;
  user_id: string;
  balance: number;
  status: string;
  memo?: string;
  created_at: string;
}

export interface Transaction {
  id: string;
  program_id: string;
  recipient_id: string;
  stellar_tx_hash: string;
  from_address: string;
  to_address: string;
  amount: number;
  asset_code: string;
  status: "pending" | "confirmed" | "failed";
  created_at: string;
  confirmed_at?: string;
}

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface CreateProgramRequest {
  name: string;
  description: string;
  organization_id: string;
  funding_amount_per_recipient: number;
  max_recipients: number;
  start_date: string;
  end_date?: string;
}

export interface AddRequirementRequest {
  requirement_type: string;
  description: string;
  condition_operator: string;
  condition_value: string;
  is_mandatory: boolean;
  verification_frequency: string;
}

export interface DisbursementRequest {
  recipient_id: string;
  program_id: string;
  amount: number;
  compliance_evaluation_id: string;
}

// ─── API Client ──────────────────────────────────────────────────────────────

export const apiClient = {
  // ─── Auth ────────────────────────────────────────────────────────────────
  auth: {
    login(email: string, password: string) {
      return post<{ access_token: string; refresh_token: string; token_type: string; expires_in: number; user: AuthUser }>(
        "/auth/login",
        { email, password }
      );
    },
    register(data: { email: string; password: string; full_name: string; role: string; organization_id?: string }) {
      return post<{ user: AuthUser } & TokenPair>("/auth/register", data);
    },
    refresh(refresh_token: string) {
      return post<TokenPair>("/auth/refresh", { refresh_token });
    },
    resetPassword(email: string) {
      return post<void>("/auth/reset-password", { email });
    },
  },

  // ─── Programs ────────────────────────────────────────────────────────────
  programs: {
    list(params?: { status?: string; cursor?: string; limit?: string }) {
      return get<PaginatedResponse<Program>>("/programs", params);
    },
    get(id: string) {
      return get<Program>(`/programs/${id}`);
    },
    create(data: CreateProgramRequest) {
      return post<Program>("/programs", data);
    },
    update(id: string, data: Partial<CreateProgramRequest>) {
      return put<Program>(`/programs/${id}`, data);
    },
    activate(id: string) {
      return post<Program>(`/programs/${id}/activate`);
    },
    pause(id: string) {
      return post<Program>(`/programs/${id}/pause`);
    },
    addRequirement(programId: string, data: AddRequirementRequest) {
      return post<ProgramRequirement>(`/programs/${programId}/requirements`, data);
    },
    fund(programId: string, amount: number) {
      return post<Transaction>(`/programs/${programId}/fund`, { amount });
    },
  },

  // ─── Applications ────────────────────────────────────────────────────────
  applications: {
    list(params?: { program_id?: string; status?: string; cursor?: string }) {
      return get<PaginatedResponse<Application>>("/applications", params);
    },
    submit(programId: string) {
      return post<Application>("/applications", { program_id: programId });
    },
  },

  // ─── Documents ───────────────────────────────────────────────────────────
  documents: {
    upload(file: File, documentType: string, submissionId: string) {
      return uploadFile<Document>("/documents/upload", file, {
        document_type: documentType,
        submission_id: submissionId,
      });
    },
    getOcrResult(documentId: string) {
      return get<OcrResult>(`/documents/${documentId}/ocr`);
    },
    verify(documentId: string, approved: boolean, notes?: string) {
      return post<void>(`/documents/${documentId}/verify`, { approved, notes });
    },
  },

  // ─── Compliance ──────────────────────────────────────────────────────────
  compliance: {
    getStatus(recipientId: string, programId: string) {
      return get<ComplianceEvaluation>(`/compliance/${recipientId}/${programId}`);
    },
    evaluate(recipientId: string, programId: string) {
      return post<ComplianceEvaluation>("/compliance/evaluate", {
        recipient_id: recipientId,
        program_id: programId,
      });
    },
  },

  // ─── Funding ─────────────────────────────────────────────────────────────
  funding: {
    getWallet() {
      return get<WalletInfo>("/funding/wallet");
    },
    createWallet() {
      return post<WalletInfo>("/funding/wallet");
    },
    cashOut(data: CashOutRequest) {
      return post<CashOutResponse>("/funding/cashout", data);
    },
    disburse(data: DisbursementRequest) {
      return post<Transaction>("/funding/disburse", data);
    },
    getTransactions(params?: { program_id?: string; cursor?: string }) {
      return get<PaginatedResponse<Transaction>>("/transactions", params);
    },
  },

  // ─── Notifications ───────────────────────────────────────────────────────
  notifications: {
    list(params?: { unread_only?: string }) {
      return get<PaginatedResponse<Notification>>("/notifications", params);
    },
    markAsRead(notificationId: string) {
      return put<void>(`/notifications/${notificationId}/read`);
    },
  },
};

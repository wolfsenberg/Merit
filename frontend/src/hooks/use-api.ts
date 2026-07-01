"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";
import {
  apiClient,
  type Program,
  type Application,
  type Notification,
  type PaginatedResponse,
  type CreateProgramRequest,
  type AddRequirementRequest,
  type DisbursementRequest,
  type ComplianceEvaluation,
  type WalletInfo,
  type Transaction,
  type OcrResult,
  type CashOutRequest,
} from "@/lib/api-client";

/**
 * TanStack Query hooks for Merit Platform API.
 * Implements stale-while-revalidate caching via query defaults.
 */

// ─── Query Keys ──────────────────────────────────────────────────────────────

export const queryKeys = {
  programs: {
    all: ["programs"] as const,
    list: (params?: { status?: string; cursor?: string; limit?: string }) =>
      ["programs", "list", params] as const,
    detail: (id: string) => ["programs", "detail", id] as const,
  },
  applications: {
    all: ["applications"] as const,
    list: (params?: { program_id?: string; status?: string; cursor?: string }) =>
      ["applications", "list", params] as const,
  },
  notifications: {
    all: ["notifications"] as const,
    list: (params?: { unread_only?: string }) =>
      ["notifications", "list", params] as const,
  },
  compliance: {
    status: (recipientId: string, programId: string) =>
      ["compliance", recipientId, programId] as const,
  },
  funding: {
    wallet: ["funding", "wallet"] as const,
    transactions: (params?: { program_id?: string; cursor?: string }) =>
      ["funding", "transactions", params] as const,
  },
  documents: {
    ocr: (documentId: string) => ["documents", "ocr", documentId] as const,
  },
} as const;

// ─── Program Hooks ───────────────────────────────────────────────────────────

export function usePrograms(
  params?: { status?: string; cursor?: string; limit?: string },
  options?: Partial<UseQueryOptions<PaginatedResponse<Program>>>
) {
  return useQuery({
    queryKey: queryKeys.programs.list(params),
    queryFn: () => apiClient.programs.list(params),
    staleTime: 30 * 1000, // 30 seconds stale-while-revalidate
    ...options,
  });
}

export function useProgram(
  id: string,
  options?: Partial<UseQueryOptions<Program>>
) {
  return useQuery({
    queryKey: queryKeys.programs.detail(id),
    queryFn: () => apiClient.programs.get(id),
    staleTime: 30 * 1000,
    enabled: !!id,
    ...options,
  });
}

export function useCreateProgram() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateProgramRequest) => apiClient.programs.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.programs.all });
    },
  });
}

export function useUpdateProgram() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateProgramRequest> }) =>
      apiClient.programs.update(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.programs.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.programs.all });
    },
  });
}

export function useActivateProgram() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.programs.activate(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.programs.detail(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.programs.all });
    },
  });
}

export function usePauseProgram() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.programs.pause(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.programs.detail(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.programs.all });
    },
  });
}

export function useAddRequirement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ programId, data }: { programId: string; data: AddRequirementRequest }) =>
      apiClient.programs.addRequirement(programId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.programs.detail(variables.programId) });
    },
  });
}

// ─── Application Hooks ───────────────────────────────────────────────────────

export function useApplications(
  params?: { program_id?: string; status?: string; cursor?: string },
  options?: Partial<UseQueryOptions<PaginatedResponse<Application>>>
) {
  return useQuery({
    queryKey: queryKeys.applications.list(params),
    queryFn: () => apiClient.applications.list(params),
    staleTime: 30 * 1000,
    ...options,
  });
}

export function useSubmitApplication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (programId: string) => apiClient.applications.submit(programId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.applications.all });
    },
  });
}

// ─── Notification Hooks ──────────────────────────────────────────────────────

export function useNotifications(
  params?: { unread_only?: string },
  options?: Partial<UseQueryOptions<PaginatedResponse<Notification>>>
) {
  return useQuery({
    queryKey: queryKeys.notifications.list(params),
    queryFn: () => apiClient.notifications.list(params),
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000, // Poll every 60s for new notifications
    ...options,
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (notificationId: string) => apiClient.notifications.markAsRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all });
    },
  });
}

// ─── Compliance Hooks ────────────────────────────────────────────────────────

export function useComplianceStatus(
  recipientId: string,
  programId: string,
  options?: Partial<UseQueryOptions<ComplianceEvaluation>>
) {
  return useQuery({
    queryKey: queryKeys.compliance.status(recipientId, programId),
    queryFn: () => apiClient.compliance.getStatus(recipientId, programId),
    staleTime: 30 * 1000,
    enabled: !!recipientId && !!programId,
    ...options,
  });
}

export function useEvaluateCompliance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ recipientId, programId }: { recipientId: string; programId: string }) =>
      apiClient.compliance.evaluate(recipientId, programId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.compliance.status(variables.recipientId, variables.programId),
      });
    },
  });
}

// ─── Funding Hooks ───────────────────────────────────────────────────────────

export function useWallet(options?: Partial<UseQueryOptions<WalletInfo>>) {
  return useQuery({
    queryKey: queryKeys.funding.wallet,
    queryFn: () => apiClient.funding.getWallet(),
    staleTime: 30 * 1000,
    ...options,
  });
}

export function useCreateWallet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.funding.createWallet(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.funding.wallet });
    },
  });
}

export function useCashOut() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CashOutRequest) => apiClient.funding.cashOut(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.funding.wallet });
      queryClient.invalidateQueries({ queryKey: queryKeys.funding.transactions() });
    },
  });
}

export function useDisburse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DisbursementRequest) => apiClient.funding.disburse(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.funding.wallet });
      queryClient.invalidateQueries({ queryKey: queryKeys.programs.all });
    },
  });
}

export function useTransactions(
  params?: { program_id?: string; cursor?: string },
  options?: Partial<UseQueryOptions<PaginatedResponse<Transaction>>>
) {
  return useQuery({
    queryKey: queryKeys.funding.transactions(params),
    queryFn: () => apiClient.funding.getTransactions(params),
    staleTime: 30 * 1000,
    ...options,
  });
}

// ─── Document Hooks ──────────────────────────────────────────────────────────

export function useOcrResult(
  documentId: string,
  options?: Partial<UseQueryOptions<OcrResult>>
) {
  return useQuery({
    queryKey: queryKeys.documents.ocr(documentId),
    queryFn: () => apiClient.documents.getOcrResult(documentId),
    staleTime: 60 * 1000, // OCR results rarely change
    enabled: !!documentId,
    ...options,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ file, documentType, submissionId }: { file: File; documentType: string; submissionId: string }) =>
      apiClient.documents.upload(file, documentType, submissionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.applications.all });
    },
  });
}

export function useVerifyDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ documentId, approved, notes }: { documentId: string; approved: boolean; notes?: string }) =>
      apiClient.documents.verify(documentId, approved, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.applications.all });
    },
  });
}

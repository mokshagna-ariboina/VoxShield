import { useMutation, useQuery } from '@tanstack/react-query';
import * as api from '../api/client';

export const useAnalyzeMutation = () => {
  return useMutation({
    mutationFn: ({ 
      file, 
      callerId,
      transactionAmount,
      recipientIsNew,
      isInternational,
      recipientAccount
    }: { 
      file: File; 
      callerId?: string;
      transactionAmount?: number;
      recipientIsNew?: boolean;
      isInternational?: boolean;
      recipientAccount?: string;
    }) =>
      api.analyzeAudio(file, callerId, transactionAmount, recipientIsNew, isInternational, recipientAccount),
  });
};

export const useChallengeMutation = () => {
  return useMutation({
    mutationFn: (callRecordId: string) => api.requestChallenge(callRecordId),
  });
};

export const useVerifyMutation = () => {
  return useMutation({
    mutationFn: ({ challengeId, audioFile }: { challengeId: string; audioFile: File }) =>
      api.verifyChallenge(challengeId, audioFile),
  });
};

export const useCalls = (page: number, pageSize: number, riskLevel?: string) => {
  return useQuery({
    queryKey: ['calls', page, pageSize, riskLevel],
    queryFn: () => api.getCalls(page, pageSize, riskLevel),
  });
};

export const useCallDetail = (callId: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['call', callId],
    queryFn: () => api.getCallDetail(callId),
    enabled,
  });
};

export const useDashboardStats = (enabled: boolean = true) => {
  return useQuery({
    queryKey: ['dashboardStats'],
    queryFn: () => api.getDashboardStats(),
    enabled,
  });
};

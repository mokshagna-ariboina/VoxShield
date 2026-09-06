import axios from 'axios';
import {
  AnalysisResponse,
  ChallengeResponse,
  VerifyResponse,
  CallListResponse,
  CallRecord,
  SpeakerProfile,
  TransactionAssessment,
  DashboardStatsResponse
} from './types';

const api = axios.create({
  baseURL: '/api',
});

export const analyzeAudio = async (
  file: File, 
  callerId?: string,
  transactionAmount?: number,
  recipientIsNew?: boolean,
  isInternational?: boolean,
  recipientAccount?: string
): Promise<AnalysisResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  if (callerId) formData.append('caller_id', callerId);
  if (transactionAmount !== undefined) formData.append('transaction_amount', transactionAmount.toString());
  if (recipientIsNew !== undefined) formData.append('recipient_is_new', recipientIsNew.toString());
  if (isInternational !== undefined) formData.append('is_international', isInternational.toString());
  if (recipientAccount) formData.append('recipient_account', recipientAccount);

  const response = await api.post<AnalysisResponse>('/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const requestChallenge = async (callRecordId: string): Promise<ChallengeResponse> => {
  const response = await api.post<ChallengeResponse>('/liveness/challenge', { call_record_id: callRecordId });
  return response.data;
};

export const verifyChallenge = async (challengeId: string, audioFile: File): Promise<VerifyResponse> => {
  const formData = new FormData();
  formData.append('file', audioFile);

  const response = await api.post<VerifyResponse>(`/liveness/verify/${challengeId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getCalls = async (page: number = 1, pageSize: number = 10, riskLevel?: string): Promise<CallListResponse> => {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (riskLevel) params.append('risk_level', riskLevel);

  const response = await api.get<CallListResponse>('/calls', { params });
  return response.data;
};

export const getCallDetail = async (callId: string): Promise<CallRecord> => {
  const response = await api.get<CallRecord>(`/calls/${callId}`);
  return response.data;
};

export const enrollSpeaker = async (audioFile: File, name: string, phone?: string): Promise<SpeakerProfile> => {
  const formData = new FormData();
  formData.append('file', audioFile);
  formData.append('name', name);
  if (phone) formData.append('phone', phone);

  const response = await api.post<SpeakerProfile>('/speakers/enroll', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const verifySpeaker = async (audioFile: File, profileId: string): Promise<VerifyResponse> => {
  const formData = new FormData();
  formData.append('file', audioFile);
  formData.append('profile_id', profileId);

  const response = await api.post<VerifyResponse>('/speakers/verify', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const assessTransaction = async (data: any): Promise<TransactionAssessment> => {
  const response = await api.post<TransactionAssessment>('/transactions/assess', data);
  return response.data;
};

export const getDashboardStats = async (): Promise<DashboardStatsResponse> => {
  const response = await api.get<DashboardStatsResponse>('/calls/stats');
  return response.data;
};

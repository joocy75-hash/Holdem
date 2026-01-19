import { create } from 'zustand';
import { withdrawApi, depositApi, WithdrawResponse } from '@/lib/api';

export type WithdrawStep = 'amount' | 'address' | 'confirm' | 'complete';

interface WithdrawState {
  // 단계
  step: WithdrawStep;

  // 환전 데이터
  amount: number | null;
  address: string;
  calculatedUsdt: string | null;
  exchangeRate: string | null;

  // 결과
  transaction: WithdrawResponse | null;

  // 상태
  isLoading: boolean;
  error: string | null;

  // Actions
  setStep: (step: WithdrawStep) => void;
  setAmount: (amount: number) => void;
  setAddress: (address: string) => void;
  fetchExchangeRate: () => Promise<void>;
  calculateUsdt: () => void;
  requestWithdraw: () => Promise<boolean>;
  reset: () => void;
  clearError: () => void;
}

export const useWithdrawStore = create<WithdrawState>((set, get) => ({
  step: 'amount',
  amount: null,
  address: '',
  calculatedUsdt: null,
  exchangeRate: null,
  transaction: null,
  isLoading: false,
  error: null,

  setStep: (step) => set({ step }),

  setAmount: (amount) => {
    set({ amount });
    get().calculateUsdt();
  },

  setAddress: (address) => set({ address }),

  fetchExchangeRate: async () => {
    try {
      const response = await depositApi.getRate();
      set({ exchangeRate: response.data.usdt_krw });
      get().calculateUsdt();
    } catch (error) {
      console.error('환율 조회 실패:', error);
      // 개발용 기본값
      set({ exchangeRate: '1400' });
    }
  },

  calculateUsdt: () => {
    const { amount, exchangeRate } = get();
    if (amount && exchangeRate) {
      const rate = parseFloat(exchangeRate);
      const usdt = (amount / rate).toFixed(2);
      set({ calculatedUsdt: usdt });
    } else {
      set({ calculatedUsdt: null });
    }
  },

  requestWithdraw: async () => {
    const { amount, address } = get();
    if (!amount || !address) {
      set({ error: '금액과 주소를 입력해주세요' });
      return false;
    }

    set({ isLoading: true, error: null });

    try {
      const response = await withdrawApi.request({
        krw_amount: amount,
        crypto_type: 'usdt',
        crypto_address: address,
      });
      set({
        transaction: response.data,
        step: 'complete',
        isLoading: false,
      });
      return true;
    } catch (error) {
      let errorMessage = '환전 요청에 실패했습니다';

      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: string } } };
        if (axiosError.response?.data?.detail) {
          errorMessage = axiosError.response.data.detail;
        }
      }

      set({ error: errorMessage, isLoading: false });
      return false;
    }
  },

  reset: () =>
    set({
      step: 'amount',
      amount: null,
      address: '',
      calculatedUsdt: null,
      transaction: null,
      isLoading: false,
      error: null,
    }),

  clearError: () => set({ error: null }),
}));

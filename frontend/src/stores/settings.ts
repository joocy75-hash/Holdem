import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SettingsState {
  bgmEnabled: boolean;
  toggleBgm: () => void;
  setBgmEnabled: (enabled: boolean) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      bgmEnabled: true,
      toggleBgm: () => set((state) => ({ bgmEnabled: !state.bgmEnabled })),
      setBgmEnabled: (enabled) => set({ bgmEnabled: enabled }),
    }),
    {
      name: 'holdem-settings',
    }
  )
);

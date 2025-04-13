import { UseToastOptions } from "@chakra-ui/react";
import { create } from "zustand";

type NotificationStatus = "success" | "error" | "warning" | "info";

interface NotificationStore {
  toast: ((options?: UseToastOptions) => string | number | undefined) | null;
  setToast: (
    toast: (options?: UseToastOptions) => string | number | undefined
  ) => void;
  showNotification: (
    title: string,
    description?: string,
    status?: NotificationStatus,
    options?: UseToastOptions
  ) => void;
  notifySuccess: (
    title: string,
    description?: string,
    options?: UseToastOptions
  ) => void;
  notifyError: (
    title: string,
    description?: string,
    options?: UseToastOptions
  ) => void;
  notifyWarning: (
    title: string,
    description?: string,
    options?: UseToastOptions
  ) => void;
  notifyInfo: (
    title: string,
    description?: string,
    options?: UseToastOptions
  ) => void;
}

export const useNotificationStore = create<NotificationStore>((set, get) => ({
  toast: null,
  setToast: (toastFn) => set({ toast: toastFn }), // Correctly store the function

  showNotification: (title, description = "", status = "info", options) => {
    const { toast } = get();
    if (toast) {
      toast({
        title,
        description,
        status,
        duration: 5000,
        isClosable: true,
        position: "top-right",
        variant: "solid",
        ...options,
      });
    } else {
      console.warn(
        "Toast function not available in notification store. Was NotificationProvider rendered?"
      );
    }
  },
  // Convenience methods remain the same
  notifySuccess: (title, description, options) =>
    get().showNotification(title, description, "success", options),
  notifyError: (title, description, options) =>
    get().showNotification(title, description, "error", options),
  notifyWarning: (title, description, options) =>
    get().showNotification(title, description, "warning", options),
  notifyInfo: (title, description, options) =>
    get().showNotification(title, description, "info", options),
}));

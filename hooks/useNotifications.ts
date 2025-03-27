import { useToast, UseToastOptions } from "@chakra-ui/react";
import { create } from "zustand";

type NotificationStatus = "success" | "error" | "warning" | "info";

interface NotificationStore {
  toast: ((options?: UseToastOptions) => void) | null;
  setToast: (toast: (options?: UseToastOptions) => void) => void;
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
  setToast: (toast) => set({ toast }),
  showNotification: (title, description = "", status = "info", options) => {
    const { toast } = get();
    toast?.({
      title,
      description,
      status,
      duration: 5000,
      isClosable: true,
      position: "top-right",
      variant: "subtle",
      ...options,
    });
  },
  notifySuccess: (title, description, options) =>
    get().showNotification(title, description, "success", options),
  notifyError: (title, description, options) =>
    get().showNotification(title, description, "error", options),
  notifyWarning: (title, description, options) =>
    get().showNotification(title, description, "warning", options),
  notifyInfo: (title, description, options) =>
    get().showNotification(title, description, "info", options),
}));

export function useNotifications() {
  const toast = useToast();

  const showNotification = (
    title: string,
    description: string = "",
    status: NotificationStatus = "info",
    options?: UseToastOptions
  ) => {
    toast({
      title: title,
      description: description,
      status: status,
      duration: 5000,
      isClosable: true,
      position: "top-right",
      variant: "subtle",
      ...options,
    });
  };

  const notifySuccess = (
    title: string,
    description?: string,
    options?: UseToastOptions
  ) => showNotification(title, description, "success", options);

  const notifyError = (
    title: string,
    description?: string,
    options?: UseToastOptions
  ) => showNotification(title, description, "error", options);

  const notifyWarning = (
    title: string,
    description?: string,
    options?: UseToastOptions
  ) => showNotification(title, description, "warning", options);

  const notifyInfo = (
    title: string,
    description?: string,
    options?: UseToastOptions
  ) => showNotification(title, description, "info", options);

  return {
    showNotification,
    notifySuccess,
    notifyError,
    notifyWarning,
    notifyInfo,
  };
}

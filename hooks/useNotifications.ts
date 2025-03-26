import { useToast, UseToastOptions } from "@chakra-ui/react";

type NotificationStatus = "success" | "error" | "warning" | "info";

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

"use client";

import { useEffect } from "react";
import { useNotificationStore } from "@/hooks/useNotifications";
import { useToast } from "@chakra-ui/react";

export const NotificationProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const toast = useToast();
  const setToast = useNotificationStore((state) => state.setToast);

  useEffect(() => {
    setToast(toast);
  }, [toast, setToast]);

  return children;
};

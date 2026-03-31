"use client";

import { useToastContext } from "@/context/toast-context";

export function useToast() {
  return useToastContext();
}

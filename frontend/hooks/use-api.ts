"use client";

import { useApiContext } from "@/context/api-context";

export function useApi() {
  return useApiContext().api;
}

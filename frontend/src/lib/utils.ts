import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** TailwindCSS 类名合并工具 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** 生成 UUID */
export function generateId(): string {
  return crypto.randomUUID?.() || Math.random().toString(36).substring(2, 15);
}

/** 格式化日期 */
export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(date));
}

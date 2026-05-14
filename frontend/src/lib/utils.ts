import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getAQIColor(aqi: number) {
  if (aqi <= 50) return 'text-primary';
  if (aqi <= 100) return 'text-secondary';
  if (aqi <= 150) return 'text-yellow-400';
  if (aqi <= 200) return 'text-tertiary-container';
  return 'text-error';
}

export function getAQIBg(aqi: number) {
  if (aqi <= 50) return 'bg-primary/20';
  if (aqi <= 100) return 'bg-secondary/20';
  if (aqi <= 150) return 'bg-yellow-400/20';
  if (aqi <= 200) return 'bg-tertiary-container/10';
  return 'bg-error/20';
}

export function getAQILabel(aqi: number) {
  if (aqi <= 50) return 'Tốt';
  if (aqi <= 100) return 'Trung bình';
  if (aqi <= 150) return 'Kém cho nhóm nhạy cảm';
  if (aqi <= 200) return 'Kém';
  return 'Nguy hại';
}

export function safeNumber(value: unknown, fallback = 0): number {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return fallback;
}

export function formatFixed(value: unknown, digits = 1, fallback = 0): string {
  return safeNumber(value, fallback).toFixed(digits);
}

export function formatNullable(value: unknown, digits = 1): string {
  if (value === null || value === undefined || value === '') return 'N/A';
  return formatFixed(value, digits);
}

export function formatDateLabel(value: unknown, fallback = 'N/A'): string {
  if (typeof value !== 'string' || value.trim() === '') return fallback;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
}

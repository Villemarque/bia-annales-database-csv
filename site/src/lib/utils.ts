export const formatTime = (seconds: number): string => {
	const hrs = Math.floor(seconds / 3600);
	const mins = Math.floor((seconds % 3600) / 60);
	const secs = seconds % 60;
	return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

export function entries<T extends Record<PropertyKey, unknown>>(obj: T) {
  return Object.entries(obj) as {
    [K in keyof T]-?: [K, T[K]];
  }[keyof T][];
}
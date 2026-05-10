/**
 * Utility functions for job-related operations
 */

export interface Store {
  id: string;
  name: string;
  brand: string;
  rating: number;
  user_ratings_total: number;
  formatted_address: string;
  coordinates: [number, number]; // [lon, lat]
  radius_km: number;
}

// clustering removed: algorithm-java will compute clusters; frontend no longer needs clustering type

export interface StoreConstraints {
  works: number[];
  doesnt_work: number[];
}

export interface GlobalConstraints {
  YEAR: number;
  SUNDAYS: number;
  MAX_WORKS: number;
  MAX_DOESNT_WORK: number;
  [storeId: string]: StoreConstraints | number;
}

/**
 * Calculate all Sundays in a given year as Date objects
 */
export function calculateSundaysInYear(year: number): Date[] {
  const sundays: Date[] = [];
  let currentDate = new Date(year, 0, 1); // Start from Jan 1

  // Find the first Sunday
  while (currentDate.getDay() !== 0) {
    currentDate.setDate(currentDate.getDate() + 1);
  }

  // Collect all Sundays in the year
  while (currentDate.getFullYear() === year) {
    sundays.push(new Date(currentDate));
    currentDate.setDate(currentDate.getDate() + 7);
  }

  return sundays;
}

/**
 * Format a date as "Sun, Jan 5"
 */
export function formatSundayDate(date: Date): string {
  const options: Intl.DateTimeFormatOptions = {
    weekday: "short",
    month: "short",
    day: "numeric",
  };
  return date.toLocaleDateString("en-US", options);
}

/**
 * Generate color based on brand name (deterministic hash-based coloring)
 */
const brandColorMap = new Map<string, string>();
const defaultBrandColors = [
  "#FF6B6B", // red
  "#4ECDC4", // teal
  "#45B7D1", // blue
  "#FFA07A", // light salmon
  "#98D8C8", // mint
  "#F7DC6F", // yellow
  "#BB8FCE", // purple
  "#85C1E2", // light blue
  "#F8B88B", // peach
  "#52C4A1", // green
];

export function getStoreColor(brand: string | undefined): string {
  const brandKey = brand?.trim() || "none";

  if (!brandColorMap.has(brandKey)) {
    if (brandKey === "none") {
      brandColorMap.set(brandKey, "#CCCCCC"); // Gray for no brand
    } else {
      const hash = brandKey
        .split("")
        .reduce((acc, char) => acc + char.charCodeAt(0), 0);
      const color =
        defaultBrandColors[hash % defaultBrandColors.length];
      brandColorMap.set(brandKey, color);
    }
  }

  return brandColorMap.get(brandKey)!;
}

/**
 * Validate store data structure
 */
export function validateStoreData(data: Record<string, any>): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (!data || typeof data !== "object") {
    return {
      valid: false,
      errors: ["Data must be a valid JSON object"],
    };
  }

  Object.entries(data).forEach(([id, store]: [string, any]) => {
    const required = [
      "name",
      "brand",
      "formatted_address",
      "coordinates",
      "user_ratings_total",
    ];
    const missing = required.filter((field) => !(field in store));

    if (missing.length > 0) {
      errors.push(
        `Store ${id} missing fields: ${missing.join(", ")}`
      );
    }

    if (
      !Array.isArray(store.coordinates) ||
      store.coordinates.length !== 2
    ) {
      errors.push(
        `Store ${id} coordinates must be [lon, lat]`
      );
    }
  });

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Validate constraints structure
 */
export function validateConstraints(
  constraints: any,
  storeIds: string[]
): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  const required = ["YEAR", "SUNDAYS", "MAX_WORKS", "MAX_DOESNT_WORK"];
  const missing = required.filter((field) => !(field in constraints));

  if (missing.length > 0) {
    errors.push(`Constraints missing global fields: ${missing.join(", ")}`);
  }

  // Optional per-store constraints validation
  storeIds.forEach((id) => {
    if (id in constraints && constraints[id]) {
      const storeConstraint = constraints[id];
      if (
        !Array.isArray(storeConstraint.works) ||
        !Array.isArray(storeConstraint.doesnt_work)
      ) {
        errors.push(
          `Store ${id} constraints must have 'works' and 'doesnt_work' arrays`
        );
      }
    }
  });

  return {
    valid: errors.length === 0,
    errors,
  };
}

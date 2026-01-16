/**
 * API Error Types and Utilities
 * 
 * Provides structured error handling for API responses.
 */

/**
 * Standard API error response structure
 */
export interface ApiErrorResponse {
  /** Error message */
  detail: string;
  /** HTTP status code */
  status?: number;
  /** Error code for programmatic handling */
  code?: string;
  /** Field-specific validation errors */
  errors?: Record<string, string[]>;
}

/**
 * Validation error for form fields
 */
export interface ValidationError {
  field: string;
  message: string;
}

/**
 * Custom API Error class with structured error data
 */
export class ApiError extends Error {
  public readonly status: number;
  public readonly code?: string;
  public readonly errors?: Record<string, string[]>;
  public readonly isApiError = true;

  constructor(
    message: string,
    status: number,
    code?: string,
    errors?: Record<string, string[]>
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.errors = errors;
  }

  /**
   * Get validation errors as flat array
   */
  getValidationErrors(): ValidationError[] {
    if (!this.errors) return [];
    
    return Object.entries(this.errors).flatMap(([field, messages]) =>
      messages.map((message) => ({ field, message }))
    );
  }

  /**
   * Check if this is a specific error type
   */
  isCode(code: string): boolean {
    return this.code === code;
  }

  /**
   * Check if this is an authentication error
   */
  isAuthError(): boolean {
    return this.status === 401 || this.status === 403;
  }

  /**
   * Check if this is a validation error
   */
  isValidationError(): boolean {
    return this.status === 422 || this.status === 400;
  }

  /**
   * Check if this is a not found error
   */
  isNotFound(): boolean {
    return this.status === 404;
  }

  /**
   * Check if this is a server error
   */
  isServerError(): boolean {
    return this.status >= 500;
  }
}

/**
 * Parse error response from API
 */
export async function parseApiError(response: Response): Promise<ApiError> {
  let errorData: ApiErrorResponse = {
    detail: 'An unexpected error occurred',
    status: response.status,
  };

  try {
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      const json = await response.json();
      errorData = {
        detail: json.detail || json.message || json.error || errorData.detail,
        status: response.status,
        code: json.code,
        errors: json.errors,
      };
    } else {
      const text = await response.text();
      if (text) {
        errorData.detail = text;
      }
    }
  } catch {
    // Use default error message if parsing fails
  }

  return new ApiError(
    errorData.detail,
    response.status,
    errorData.code,
    errorData.errors
  );
}

/**
 * Type guard to check if error is an ApiError
 */
export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError || (error as ApiError)?.isApiError === true;
}

/**
 * Get user-friendly error message
 */
export function getErrorMessage(error: unknown): string {
  if (isApiError(error)) {
    return error.message;
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  if (typeof error === 'string') {
    return error;
  }
  
  return 'An unexpected error occurred';
}

/**
 * Common error codes
 */
export const ErrorCodes = {
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  NOT_FOUND: 'NOT_FOUND',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  RATE_LIMITED: 'RATE_LIMITED',
  SERVER_ERROR: 'SERVER_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
} as const;

export type ErrorCode = typeof ErrorCodes[keyof typeof ErrorCodes];

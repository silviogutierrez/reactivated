export interface SerializedError {
    message: string;
    stack: string | null;
}

export interface SSRErrorResponse {
    error: SerializedError;
}

export const serializeError = (error: Error): SerializedError => ({
    message: error.toString(),
    stack: error.stack || null,
});

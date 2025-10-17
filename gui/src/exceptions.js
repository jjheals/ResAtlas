
/**
 * @abstract Raised when a date is not in valid YYYY-MM-DD format. 
 */
export class InvalidDateError extends Error { 
    constructor(message) {
        super(message);
        this.name = 'InvalidDateError';
    }
}

/**
 * @abstract Raised when there is an error with hitting the local API (likely a network error).
 */
export class APIError extends Error { 
    constructor(message) { 
        super(message);
        this.name = 'APIError';
    }
}
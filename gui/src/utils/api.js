import { InvalidDateError, APIError } from "../exceptions";
import { isValidDateTime } from "./general";
import { apiUri } from "../globalConstants";

/**
 * @function getReservations 
 * @abstract Method to retrieve all reservations starting on the given [startDate]/[startTime] and ending on the given 
 * [endDate]/[endTime] (inclusive). 
 * 
 * @param { String } startDateTime - the beginning of the date frame (inclusive) in YYYY-MM-DDTHH:MM:SS format.
 * @param { Number } endDateTime - the beginning of the timeframe within the range [0,24], and in 0.25 increments. 
 * @returns { Array<Object> } - an Array of dictionaries where each is a reservation. 
 * 
 * @throws { RangeError } if the given [startDate] OR [endDate] is out of a reasonable range, OR if the given datetime falls 
 * outside of what the API says is acceptable.
 * @throws { InvalidDateError } if the given [startDate]/[endDate] is not a valid date in YYYY-MM-DDTHH:MM:SS format.
 * @throws { APIError } if there is an error retrieving the data from the API.
 * @throws { Error } if there is some other unexpected error during the process. 
 */
export async function getReservations(startDateTime, endDateTime) { 

    // Validate the dates and times
    if(!isValidDateTime(startDateTime) || !isValidDateTime(endDateTime)) {
        throw new InvalidDateError(`One of the given dates is not valid. Given [startDateTime = ${startDateTime}], [endDateTime = ${endDateTime}].`)
    }

    try { 
        // Hit the API to get the reservations 
        const response = await fetch(`${apiUri}/get-reservations?startDateTime=${startDateTime}&endDateTime=${endDateTime}`)

        // Check response 
        if (!response.ok) throw new APIError(`Error retrieving reservations (getReservations()) - Status: ${response.status}`);

        // Extract data from response 
        const data = await response.json();
        console.log(data);
        
    } catch (error) {
        console.error('Unexpected error in getReservations()', error);
        throw error;
    }
}
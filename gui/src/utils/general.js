import { InvalidDateError } from "../exceptions";


/**
 * @function isValidDateTime
 * @abstract Checks whether the given string is a valid datetime string in YYYY-MM-DDTHH:MM:SS format. 
 * @param { String } str - a datetime string. 
 * @returns { boolean } [true] if the given datetime is valid, false otherwise.
 */
export function isValidDateTime(str) {

  // Check the exact format using a regular expression
  const regex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/;
  if (!regex.test(str)) return false;

  // Split date and time parts
  const [datePart, timePart] = str.split('T');
  const [year, month, day] = datePart.split('-').map(Number);
  const [hour, minute, second] = timePart.split(':').map(Number);

  // Validate ranges
  if (month < 1 || month > 12) return false;
  if (hour < 0 || hour > 23) return false;
  if (minute < 0 || minute > 59 || !isQuarterHour(minute)) return false;    // NOTE: minutes should always be a quarter hour (0, 15, 30, 45)
  if (second != 0) return false;                                            // NOTE: seconds should always be 0

  // Create Date object
  const date = new Date(`${datePart}T${timePart}`);

  // Validate actual date components (to avoid things like Feb 30 -> Mar 2)
  return (
    date.getFullYear() === year &&
    date.getMonth() + 1 === month &&
    date.getDate() === day &&
    date.getHours() === hour &&
    date.getMinutes() === minute &&
    date.getSeconds() === second
  );
}


/**
 * @function isQuarterHour
 * @param { Number } minutes 
 * @returns { Boolean } [true] if the given number is a quarter hour (0, 15, 30, 45), [false] otherwise
 */
function isQuarterHour(minutes) {
  return minutes % 15 === 0;
}


/**
 * @function isDateTimeInRange
 * @abstract Checks whether the given [dateTimeStr] falls within the [rangeStartStr], [rangeEndStr] (inclusive).
 * @param { String } dateTimeStr - the datetime to check in YYYY-MM-DDTHH:MM:SS format.
 * @param { String } rangeStartStr - the start of the valid range in YYYY-MM-DDTHH:MM:SS format.
 * @param { String } rangeEndStr - the end of the valid range in in YYYY-MM-DDTHH:MM:SS format.
 * @returns { Boolean } [true] if the given [dateTimeStr] falls within the range, [false] otherwise.
 */
function isDateTimeInRange(dateTimeStr, rangeStartStr, rangeEndStr) {

  // Convert all strings to Date objects
  const dateTime = new Date(dateTimeStr);
  const rangeStart = new Date(rangeStartStr);
  const rangeEnd = new Date(rangeEndStr);

  // Check for invalid dates (NaN)
  if (isNaN(dateTime) || isNaN(rangeStart) || isNaN(rangeEnd)) {
    throw new InvalidDateError("Invalid datetime string provided");
  }

  // Compare timestamps (milliseconds since epoch)
  return dateTime >= rangeStart && dateTime <= rangeEnd;
}

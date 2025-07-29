from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List
from datetime import datetime
import pytz

app = FastAPI(
    title="Timezone Converter API",
    description="REST API for converting times between different global time zones.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Time Zone Conversion", "description": "Endpoints for converting times between global time zones."},
        {"name": "Utility", "description": "Health check and utility endpoints"}
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PUBLIC_INTERFACE
class TimeConversionRequest(BaseModel):
    """Request body for converting time from one timezone to another."""
    time: str = Field(..., description="Time in source timezone, format: YYYY-MM-DD HH:MM (24hr format)")
    source_timezone: str = Field(..., description="Source timezone (e.g., 'UTC', 'America/New_York'). Must be a valid tz name.")
    target_timezone: str = Field(..., description="Target timezone (e.g., 'Asia/Kolkata'). Must be a valid tz name.")

    @validator('time')
    def validate_time_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M")
        except Exception:
            raise ValueError("time must be in format 'YYYY-MM-DD HH:MM' (24hr)")
        return v

    @validator('source_timezone', 'target_timezone')
    def validate_timezone(cls, v):
        if v not in pytz.all_timezones:
            raise ValueError(f"{v} is not a recognized timezone.")
        return v

# PUBLIC_INTERFACE
class TimeConversionResponse(BaseModel):
    """Response model for converted time."""
    original_time: str = Field(..., description="Input time in the source timezone")
    converted_time: str = Field(..., description="Converted time in the target timezone, format: YYYY-MM-DD HH:MM")
    source_timezone: str = Field(..., description="Source timezone")
    target_timezone: str = Field(..., description="Target timezone")

# PUBLIC_INTERFACE
class TimezonesResponse(BaseModel):
    """Response model for available time zones."""
    timezones: List[str] = Field(..., description="List of supported time zone names")

@app.get("/", tags=["Utility"])
def health_check():
    """Health check endpoint for the API.

    Returns a simple JSON message indicating that the API is running.
    """
    return {"message": "Healthy"}

# PUBLIC_INTERFACE
@app.get("/timezones", response_model=TimezonesResponse, tags=["Time Zone Conversion"])
def list_timezones():
    """
    Returns a list of all supported time zone names.

    Returns:
        timezones: List of string time zone names.
    """
    return {"timezones": pytz.all_timezones}

# PUBLIC_INTERFACE
@app.post(
    "/convert-time",
    response_model=TimeConversionResponse,
    tags=["Time Zone Conversion"],
    summary="Convert time between time zones",
    description="Converts a given date and time from a source time zone to a target time zone."
)
def convert_time(request: TimeConversionRequest):
    """
    Converts a given time from the source timezone to the target timezone.

    Args:
        request: An object containing time, source_timezone, and target_timezone.

    Returns:
        JSON object with original and converted time in the corresponding time zones.

    Errors:
        400 - Invalid input or timezone not recognized.
    """
    try:
        # Parse input time in source timezone
        input_dt_naive = datetime.strptime(request.time, "%Y-%m-%d %H:%M")
        src_tz = pytz.timezone(request.source_timezone)
        tgt_tz = pytz.timezone(request.target_timezone)
        input_dt = src_tz.localize(input_dt_naive)
        # Convert to target timezone
        converted_dt = input_dt.astimezone(tgt_tz)
        return TimeConversionResponse(
            original_time=input_dt.strftime("%Y-%m-%d %H:%M"),
            converted_time=converted_dt.strftime("%Y-%m-%d %H:%M"),
            source_timezone=request.source_timezone,
            target_timezone=request.target_timezone,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid input or time zone error: {str(e)}")

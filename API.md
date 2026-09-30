# Hotel Management API

The JSON API is rooted at /api/v1/. The health endpoint is /api/v1/health/.
Send Content-Type: application/json for JSON requests. Authenticated requests use:

    Authorization: Token <token returned by /api/v1/auth/login/>

The CORS middleware allows http://localhost:3000 and http://localhost:5173 by default.
Set CORS_ALLOWED_ORIGINS to a comma-separated list of exact frontend origins when deploying.

Start the backend from the project directory with:

    .venv/Scripts/python.exe manage.py migrate
    .venv/Scripts/python.exe manage.py runserver

Create or promote staff accounts through Django admin or the existing user administration workflow.
Set DJANGO_SECRET_KEY, DJANGO_DEBUG=False, and DJANGO_ALLOWED_HOSTS for deployment.

## Authentication

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | /api/v1/ | Health response (200, {"ok":true,...}) |
| POST | /api/v1/auth/register/ | Create an account (201 means account created; invalid fields return 400) |
| POST | /api/v1/auth/login/ | Send username and password; success returns token and safe user data |
| POST | /api/v1/auth/logout/ | Delete the current token (204 means logged out) |
| GET/PATCH/PUT | /api/v1/auth/me/ | Read or update the current user's profile |

## Catalog and inventory

These endpoints allow public GET requests. Create, update, and delete operations require a staff token.

| Resource | Endpoint | Notes |
| --- | --- | --- |
| Hotels | /api/v1/hotels/ | Hotel records |
| Amenities | /api/v1/amenities/ | Hotel amenity names |
| Room categories | /api/v1/room-categories/ | Public users see only Active categories |
| Rooms | /api/v1/rooms/ | Room includes category details and media metadata |
| Room media | /api/v1/room-media/ | Metadata only; the current model has no file/image upload field |
| Services | /api/v1/services/?hotel=<id> | Service menu, optionally filtered by hotel |
| Service items | /api/v1/service-items/ | Menu items include price and availability |

Room availability can be queried with ISO date-times, for example:
/api/v1/rooms/?available=true&check_in=2026-11-01T15:00:00Z&check_out=2026-11-03T11:00:00Z.
The API excludes rooms booked during an overlapping stay. Invalid or reversed dates return an empty list.

Room categories are global in the existing database schema and are not linked to a hotel.
Likewise, room categories do not identify a hotel. Booking requests therefore validate room
availability and guest capacity, but cannot enforce that a selected room belongs to the supplied hotel.

## Bookings

All booking endpoints require a token. Customers see only their own bookings; staff can see all.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET/POST | /api/v1/bookings/ | List bookings or create a pending online booking |
| GET | /api/v1/bookings/<id>/ | Read booking and its room lines |
| PATCH/PUT | /api/v1/bookings/<id>/ | Staff-only booking edits, including discount and tax |
| POST | /api/v1/bookings/<id>/cancel/ | Cancel an eligible booking |
| POST | /api/v1/bookings/<id>/set_status/ | Staff-only status transition with {"status":"CONFIRMED"} |
| POST | /api/v1/bookings/<id>/check_in/ | Staff check-in for a confirmed booking |
| POST | /api/v1/bookings/<id>/check_out/ | Staff check-out for an in-house booking |
| GET/POST/PATCH/DELETE | /api/v1/booking-rooms/ | Staff-only room-line adjustments |

Create a booking with hotel, check_in, check_out, number_of_guests, and room_ids:

    {
      "hotel": 1,
      "check_in": "2026-11-01T15:00:00Z",
      "check_out": "2026-11-03T11:00:00Z",
      "number_of_guests": 2,
      "room_ids": [4],
      "special_requests": "Late arrival"
    }

The server calculates room prices, subtotal, and total. Invalid dates, past check-in, insufficient
capacity, occupied rooms, or missing room selection return 400 with field errors. The model uses
date-times, so the resulting nightly count is calculated from the dates.

## Service orders

All order endpoints require a token. Customers can order for their own active booking; staff can
view/process all orders and adjust lines.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET/POST | /api/v1/orders/ | List orders or create an order |
| GET | /api/v1/orders/<id>/ | Read order lines and server-calculated totals |
| POST | /api/v1/orders/<id>/cancel/ | Customer cancellation while pending |
| POST | /api/v1/orders/<id>/set_status/ | Staff-only status change |
| GET/POST/PATCH/DELETE | /api/v1/order-items/ | Staff-only order-line maintenance |

Create an order using booking and lines:

    {
      "booking": 12,
      "lines": [
        {"item": 7, "quantity": 2}
      ]
    }

Prices come from the service catalog, and item availability plus matching hotel ownership are
validated by the API and model. The booking total is refreshed after order changes or cancellation.

## Payments

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET/POST | /api/v1/payments/ | List own payment attempts or create a pending attempt |
| POST | /api/v1/payments/<id>/settle/ | Staff-only reconciliation with status and optional transaction_reference |

Payment creation accepts booking, method, and optional amount. The default amount is the
outstanding booking balance. A successful create means only that a pending attempt was recorded.
No card processor or bank integration is configured; staff must record SUCCEEDED, FAILED, or
REFUNDED after confirming settlement outside this API.

## Response meaning

Successful reads and updates return JSON with a 2xx status. Create operations return 201;
successful deletion/logout returns 204. Invalid input and unavailable business-state changes return
400 with a detail or field-level error. Missing/invalid authentication returns 401, and a
logged-in user lacking permission receives 403. A missing record returns 404.

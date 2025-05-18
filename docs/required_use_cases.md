## **1️⃣ Workshops**

The system must be able to:

1. **Create a Workshop**

   * An admin can create a new workshop with the following details:

     * Title of the workshop
     * Date when the workshop takes place
     * Time the workshop starts
     * Location of the workshop
     * Maximum number of family slots
     * Maximum number of child slots

2. **View Available Workshops**

   * A guardian can view a list of all upcoming workshops.
   * The list should include:

     * Title, Date, Time, Location
     * Remaining family slots
     * Remaining child slots

3. **Edit a Workshop**

   * An admin can edit the details of an existing workshop:

     * Title
     * Date
     * Time
     * Location
     * Maximum families
     * Maximum children
   * If slots are reduced, any affected bookings should be flagged for admin attention.

4. **Update Workshop Availability**

   * When bookings are made or cancelled, the system must automatically:

     * Reduce the available family slots and child slots.
     * Increase the available slots when a booking is cancelled.

5. **Delete a Workshop**

   * An admin can remove a workshop from availability.
   * If there are existing bookings, all guardians should be notified.
   * Slots should be released back into the system.

6. **Prevent Overbooking**

   * The system must not allow bookings that exceed the maximum number of families or children.
   * If a booking request comes in and there are not enough slots, it should fail gracefully with an error message.

---

## **2️⃣ Bookings**

The system must be able to:

1. **Create a Booking**

   * A guardian can book slots for their children in a workshop.
   * The booking form must capture:

     * Guardian Details:

       * Name
       * Email
       * Phone Number
       * Postcode
     * Children Details:

       * First Name
       * Age

2. **View All Bookings for a Workshop**

   * An admin can see all the bookings for a specific workshop.
   * This view must include:

     * Guardian's name and contact information
     * Names and ages of the children booked

3. **Cancel a Booking**

   * An admin or a guardian can cancel a booking.
   * When this happens:

     * The slots are released back to the workshop
     * The guardian receives a cancellation confirmation
     * The admin is notified

4. **Prevent Duplicate Bookings for the Same Child**

   * The system must not allow the same child to be booked into the same workshop more than once.

---

## **3️⃣ Guardians (Parents)**

The system must be able to:

1. **Register a Guardian**

   * A guardian's information should be captured during the first booking:

     * Name
     * Email
     * Phone Number
     * Postcode

2. **Link Bookings to Guardians**

   * Each booking must be associated with a registered guardian.
   * This allows easy searching and filtering by the admin.

3. **Update Guardian Information**

   * If the guardian needs to change their contact details, the system should allow updates.

---

## **4️⃣ Admin Management (Role-Based Access)**

The system must be able to:

1. **Authenticate Admins**

   * Only admins can:

     * Create, edit, or delete workshops
     * View all bookings for a workshop
     * Cancel any booking

2. **Role-Based Access Control**

   * If a non-admin tries to perform admin actions, the system must reject the request with an appropriate error.

---

## **5️⃣ Notifications**

The system must be able to:

1. **Send Confirmation Emails**

   * When a booking is successful, an email confirmation should be sent to the guardian.
   * The email must include:

     * Workshop title
     * Date, time, and location
     * Names of the children booked
     * Guardian contact details

2. **Send Admin Notifications**

   * When a booking is created, edited, or cancelled, an email should be sent to the admin for visibility.

3. **Send Workshop Cancellation Notices**

   * If a workshop is deleted, all guardians with bookings must be notified via email.

---

## **6️⃣ Database Consistency**

The system must be able to:

1. **Persist Data Correctly**

   * All workshops, bookings, and guardian information should be reliably stored.
   * If any failure occurs during save operations, the system should roll back changes.

2. **Prevent Orphaned Data**

   * If a workshop is deleted, all linked bookings should also be safely removed or flagged.
   * No "dead" references should remain in the database.

---

## **7️⃣ Validation Rules**

The system must be able to:

1. **Validate Input Data**

   * Title, Date, Time, and Location must not be empty for a workshop.
   * Guardian details must be complete and valid.
   * Child names and ages must be filled in correctly.

2. **Handle Invalid Operations Gracefully**

   * If an admin tries to edit a workshop with an invalid date, it should fail gracefully.
   * If a guardian tries to book a slot that is already full, it should show an appropriate message.

---

## **8️⃣ Edge Cases to Cover:**

1. **Booking the Last Available Slot**

   * If two people try to book the last slot at the same time, one should succeed, and the other should gracefully fail.

2. **Deleting a Workshop with Active Bookings**

   * The system should send notifications to guardians and release the slots.

3. **Editing a Workshop that Affects Bookings**

   * If max slots are reduced, any affected bookings should be flagged for admin attention.

4. **Cancelling a Workshop with Active Bookings**

   * Admin should be able to select whether guardians are refunded or offered another slot.
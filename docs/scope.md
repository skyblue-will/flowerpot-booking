### **Project Vision:**

A streamlined, self-contained Workshop Booking System that allows:

1. **Guardians (Parents)** to book slots for children in workshops (no login required).
2. **Admin Users** to manage workshop schedules and capacities.
3. **View, Book, and Manage** all workshop sessions.
4. **Configurable maximum family slots** and **maximum children slots** per workshop.

---

### **Core Concepts:**

#### 1️⃣ **Workshop**

* Represents a scheduled event for children.
* Holds maximum family capacity and maximum child capacity.
* Tracks current reservations.

#### 2️⃣ **Booking**

* Represents a family reservation for a workshop.
* Contains Guardian details and Children details (First name, Age).

#### 3️⃣ **Guardian**

* Represents the parent or guardian making the booking.
* Holds contact information.

#### 4️⃣ **Admin**

* Manages workshop schedules, bookings, and capacities.

---

### **Use Cases (Core Logic):**

#### 1️⃣ **ViewWorkshops.py**

* Displays available workshops and remaining slots.
* Pulls from the current list of active workshops.

#### 2️⃣ **CreateWorkshop.py**

* Admin creates a new workshop.
* Defines maximum family slots and maximum child slots.

#### 3️⃣ **CreateBooking.py**

* Creates a booking for a selected workshop.
* Ensures available family and child slots exist before confirmation.

#### 4️⃣ **CancelBooking.py**

* Cancels a booking and releases the slots back to the workshop.

#### 5️⃣ **UpdateWorkshopAvailability.py**

* Updates the slots dynamically when bookings are made or cancelled.

#### 6️⃣ **DeleteWorkshop.py**

* Removes a workshop from availability and notifies Guardians if required.

---

### **Entities (Pure Data Models):**

#### **WorkshopEntity.py**

* ID
* Title
* Date
* Max Families
* Max Children
* Current Families
* Current Children

#### **BookingEntity.py**

* ID
* Workshop ID
* Guardian Name
* Children (List of objects with Name, Age)

#### **GuardianEntity.py**

* ID
* Name
* Email
* Phone

---

### **Flow of a Booking:**

1️⃣ **View Workshops →**

* The Guardian selects an available workshop.

2️⃣ **Create Booking →**

* Guardian enters details and children’s names and ages.
* System checks slot availability.
* If available, booking is confirmed.

3️⃣ **Update Availability →**

* Workshop slots are reduced accordingly.

4️⃣ **Cancel Booking (if needed) →**

* Slots are released back to the workshop.

5️⃣ **Admin Management →**

* Admin can manually create, view, and delete workshops.
* Admin can manually adjust slots if required.

---

### **Database Structure (Minimal):**

#### **Workshops Table:**

* `id` (Primary Key)
* `title`
* `date`
* `max_families`
* `max_children`
* `current_families`
* `current_children`

#### **Bookings Table:**

* `id` (Primary Key)
* `workshop_id` (Foreign Key → Workshops)
* `guardian_name`
* `children`

#### **Guardians Table:**

* `id` (Primary Key)
* `name`
* `email`
* `phone`

---

### **Constraints:**

1. **Maximum of 4 families per workshop.**
2. **Maximum of 8 children per workshop.**
3. **Admin can adjust these settings** per workshop if needed.

---

### **Acceptance Criteria:**

1. **View Workshops:** Guardians can see available workshops and remaining slots.
2. **Create Workshop:** Admin can create a workshop and set capacities.
3. **Create Booking:** Booking fails if there are no available slots.
4. **Cancel Booking:** Slots are released back to the workshop.
5. **Delete Workshop:** Workshop is removed from availability.

---

### **Expected Behaviour:**

1. If a family cancels, the slots are immediately available for others.
2. If a workshop is deleted, all bookings are cancelled with notifications sent.
3. Admin views are always real-time and reflect current availability.

---

### **Next Steps:**

1. Build isolated tests for each use case (View, Create, Cancel, Delete).
2. Implement database stubs for quick validation.
3. Ensure LLM can read and understand this flow without additional context.
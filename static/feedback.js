document.addEventListener("DOMContentLoaded", function () {
  const stars = document.querySelectorAll(".star");
  const ratingInput = document.getElementById("rating");
  const feedbackForm = document.getElementById("feedbackForm");
  const submitButton = feedbackForm.querySelector("button[type='submit']");

  let selectedRating = 0;

  stars.forEach((star, index) => {
    star.addEventListener("click", function () {
      selectedRating = parseInt(this.getAttribute("data-value"));
      ratingInput.value = selectedRating;
      updateStars(selectedRating);
    });

    star.addEventListener("mouseover", function () {
      if (selectedRating === 0) {
        highlightStars(index);
      }
    });

    star.addEventListener("mouseout", function () {
      if (selectedRating === 0) {
        resetStars();
      }
    });
  });

  function updateStars(rating) {
    stars.forEach((star, index) => {
      if (index < rating) {
        star.classList.add("active");
        star.style.fill = "gold";
      } else {
        star.classList.remove("active");
        star.style.fill = "#ddd";
      }
    });
  }

  function highlightStars(index) {
    stars.forEach((star, i) => {
      if (i <= index) {
        star.style.fill = "gold";
      } else {
        star.style.fill = "#ddd";
      }
    });
  }

  function resetStars() {
    stars.forEach((star) => {
      star.style.fill = "#ddd";
      star.classList.remove("active");
    });
  }
  function fetchRatings() {
    window.db.collection("feedback").onSnapshot((snapshot) => {
      let totalReviews = snapshot.size;
      let ratingCounts = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
      let totalRating = 0;

      snapshot.forEach((doc) => {
        let rating = doc.data().rating;
        if (ratingCounts[rating] !== undefined) {
          ratingCounts[rating]++;
          totalRating += rating;
        }
      });

      let averageRating =
        totalReviews > 0 ? (totalRating / totalReviews).toFixed(1) : "0.0";

      // Update HTML
      document.getElementById("average-rating").innerText = averageRating;
      document.getElementById("total-reviews").innerText = totalReviews;

      // Update progress bars
      Object.keys(ratingCounts).forEach((rating) => {
        let percentage =
          totalReviews > 0 ? (ratingCounts[rating] / totalReviews) * 100 : 0;
        document.getElementById(`stars-${rating}`).style.width =
          percentage + "%";
        document.getElementById(
          `stars-${rating}`
        ).innerText = `${percentage.toFixed(1)}%`;
      });
    });
  }

  // Wait for Firebase to be initialized
  function waitForFirebase() {
    return new Promise((resolve, reject) => {
      const checkFirebase = setInterval(() => {
        if (window.db) {
          clearInterval(checkFirebase);
          console.log("✅ Firebase is initialized");
          resolve();
        }
      }, 500);
      setTimeout(() => {
        clearInterval(checkFirebase);
        reject(new Error("❌ Firebase took too long to initialize!"));
      }, 5000);
    });
  }

  waitForFirebase()
    .then(() => fetchRatings())
    .then(() => {
      feedbackForm.addEventListener("submit", function (event) {
        event.preventDefault();

        // Disable button to prevent multiple clicks
        submitButton.disabled = true;
        submitButton.innerText = "Submitting...";

        const name = document.getElementById("name").value.trim();
        const message = document.getElementById("message").value.trim();

        if (!selectedRating) {
          Swal.fire({
            title: "Warning",
            text: "Please select a rating before submitting!",
            icon: "warning",
            confirmButtonText: "OK",
          });
          submitButton.disabled = false;
          submitButton.innerText = "Submit";
          return;
        }

        if (message === "") {
          Swal.fire({
            title: "Warning",
            text: "Feedback cannot be empty, please provide some feedback",
            icon: "warning",
            confirmButtonText: "OK",
          });
          submitButton.disabled = false;
          submitButton.innerText = "Submit";
          return;
        }

        // Check if the user is offline
        if (!navigator.onLine) {
          Swal.fire({
            title: "No Internet Connection",
            text: "You are offline. Please check your internet connection and try again.",
            icon: "warning",
            confirmButtonText: "OK",
          });
          submitButton.disabled = false;
          submitButton.innerText = "Submit";
          return;
        }

        // Save to Firebase
        window.db
          .collection("feedback")
          .add({
            name: name,
            rating: selectedRating,
            message: message,
            timestamp: firebase.firestore.FieldValue.serverTimestamp(),
          })
          .then(() => {
            Swal.fire({
              title: "Success",
              text: "✅ Feedback submitted successfully!",
              icon: "success",
              confirmButtonText: "OK",
            });

            feedbackForm.reset();
            resetStars();

            // Re-enable submit button after successful submission
            submitButton.innerText = "Submit";
            submitButton.disabled = false;
          })
          .catch((error) => {
            console.error("Error adding document: ", error);
            Swal.fire({
              title: "Error",
              text: "❌ Error submitting feedback!",
              icon: "error",
              confirmButtonText: "OK",
            });

            // Re-enable submit button in case of failure
            submitButton.innerText = "Submit";
            submitButton.disabled = false;
          });
      });
    })
    .catch((error) => {
      console.error(error.message);
    });
});

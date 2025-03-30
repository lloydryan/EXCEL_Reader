document.addEventListener("DOMContentLoaded", function () {
  const stars = document.querySelectorAll(".star");
  const ratingInput = document.getElementById("rating");
  const feedbackForm = document.getElementById("feedbackForm");
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
    .then(() => {
      feedbackForm.addEventListener("submit", function (event) {
        event.preventDefault();

        const name = document.getElementById("name").value.trim();
        const message = document.getElementById("message").value.trim();

        if (!selectedRating) {
          Swal.fire({
            title: "Warning",
            text: "Please select a rating before submitting!",
            icon: "warning",
            confirmButtonText: "OK",
          });
          return;
        }

        if (message === "") {
          Swal.fire({
            title: "Warning",
            text: "Feedback cannot be empty, please provide some feedback",
            icon: "warning",
            confirmButtonText: "OK",
          });
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
          })
          .catch((error) => {
            console.error("Error adding document: ", error);
            Swal.fire({
              title: "Error",
              text: "❌ Error submitting feedback!",
              icon: "error",
              confirmButtonText: "OK",
            });
          });
      });
    })
    .catch((error) => {
      console.error(error.message);
    });
});

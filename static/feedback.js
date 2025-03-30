document.addEventListener("DOMContentLoaded", function () {
  const stars = document.querySelectorAll(".star");
  const ratingInput = document.getElementById("rating");
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

  document
    .getElementById("feedbackForm")
    .addEventListener("submit", function (event) {
      if (!selectedRating) {
        alert("Please select a rating!");
        event.preventDefault();
        return;
      }
      alert("You have given " + selectedRating + " star(s)!");
    });
});

document.addEventListener("DOMContentLoaded", function () {
    // Display a welcome message if the user is logged in
    const welcomeMessage = document.getElementById("welcome-message");
    const user = sessionStorage.getItem("username"); // Assuming you store username in session storage

    if (user) {
        welcomeMessage.textContent = `Welcome, ${user}!`;
        welcomeMessage.style.display = "block"; // Show the welcome message
    } else {
        welcomeMessage.style.display = "none"; // Hide the message if not logged in
    }

    // Handle logout functionality
    const logoutButton = document.getElementById("logout-button");
    if (logoutButton) {
        logoutButton.addEventListener("click", function () {
            sessionStorage.removeItem("username"); // Clear user session
            window.location.href = "login.html"; // Redirect to login page
        });
    }

    // Optional: Smooth scrolling for navigation links
    const navLinks = document.querySelectorAll("a[href^='#']");
    navLinks.forEach(link => {
        link.addEventListener("click", function (event) {
            event.preventDefault();
            const targetId = this.getAttribute("href");
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: "smooth" });
            }
        });
    });
});


document.addEventListener("DOMContentLoaded", function () {
    // Function to validate form fields
    function validateForm(form) {
        let valid = true;
        const inputs = form.querySelectorAll("input[required]");

        inputs.forEach(input => {
            if (!input.value.trim()) {
                valid = false;
                input.classList.add("error");
                input.nextElementSibling.textContent = `${input.placeholder} is required`;
            } else {
                input.classList.remove("error");
                input.nextElementSibling.textContent = "";
            }
        });

        return valid;
    }

    // Handle form submission for registration
    const registerForm = document.querySelector("form[action='/register']");
    if (registerForm) {
        registerForm.addEventListener("submit", function (event) {
            if (!validateForm(registerForm)) {
                event.preventDefault(); // Prevent form submission if validation fails
            }
        });
    }

    // Handle form submission for login
    const loginForm = document.querySelector("form[action='/login']");
    if (loginForm) {
        loginForm.addEventListener("submit", function (event) {
            if (!validateForm(loginForm)) {
                event.preventDefault(); // Prevent form submission if validation fails
            }
        });
    }

    // Optional: Clear error messages on input focus
    const inputs = document.querySelectorAll("input");
    inputs.forEach(input => {
        input.addEventListener("focus", function () {
            input.classList.remove("error");
            input.nextElementSibling.textContent = ""; // Clear error message
        });
    });
});

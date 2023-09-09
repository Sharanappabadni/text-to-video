// Retrieve user data from session/local storage or global state
document.addEventListener('DOMContentLoaded', function () {
    // Retrieve user data from local storage
    const userData = JSON.parse(localStorage.getItem('loginData'));

    if (userData && userData.email) {
        const userEmailElement = document.getElementById('user-email');
        // Set the content of the element to the user's email
        userEmailElement.textContent = `User Email: ${userData.email}`;
    } else {
        // Handle the case where userData is not available
        console.log("User data is not available.");
    }
});
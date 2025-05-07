// Connect to Socket.IO server
// Ensure the URL matches your server address and port
const socket = io.connect(window.location.protocol + '//' + document.domain + ':' + location.port);

socket.on('connect', () => {
    console.log('Connected to WebSocket server');
    // Example: If on an auction detail page, join the specific room
    // This requires the auction_id to be available in the HTML or URL
    // const auctionIdElement = document.getElementById('auction-id');
    // if (auctionIdElement) {
    //     const auctionId = auctionIdElement.value;
    //     socket.emit('join_auction', { auction_id: auctionId });
    // }
});

socket.on('disconnect', () => {
    console.log('Disconnected from WebSocket server');
});

socket.on('update_bid', (data) => {
    console.log('Received bid update:', data);
    // Find the auction item on the page to update
    // This assumes each item has a unique identifier, e.g., data-auction-id
    const auctionItem = document.querySelector(`.auction-item[data-auction-id="${data.auction_id}"]`);
    if (auctionItem) {
        const currentBidElement = auctionItem.querySelector('.current-bid'); // Need to add this class
        const timeLeftElement = auctionItem.querySelector('.time-left');     // Need to add this class

        if (currentBidElement) {
            currentBidElement.textContent = `Current Bid: $${parseFloat(data.new_price).toFixed(2)}`;
            // Add a visual cue for the update
            highlightUpdate(auctionItem);
        }
        // Optionally update time left if provided in data
        // if (timeLeftElement && data.time_left) {
        //     timeLeftElement.textContent = `Time Left: ${data.time_left}`;
        // }
    } else {
        console.warn(`Auction item not found on page for update: ${data.auction_id}`);
    }
});

// Function to add a temporary highlight effect
function highlightUpdate(element) {
    element.classList.add('updated');
    setTimeout(() => {
        element.classList.remove('updated');
    }, 1000); // Remove highlight after 1 second
}

console.log('Auction System Frontend Script Loaded!');

// Basic validation example (can be expanded)
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.querySelector('main form[action*="login"]'); // More specific selector
    const registerForm = document.querySelector('main form[action*="register"]'); // More specific selector

    if (loginForm) {
        loginForm.addEventListener('submit', (event) => {
            const username = loginForm.querySelector('#username');
            const password = loginForm.querySelector('#password');
            let isValid = true;

            if (!username.value.trim()) {
                alert('Username is required.');
                isValid = false;
            }
            if (!password.value.trim()) {
                alert('Password is required.');
                isValid = false;
            }

            if (!isValid) {
                event.preventDefault(); // Stop form submission if invalid
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', (event) => {
            const username = registerForm.querySelector('#username');
            const email = registerForm.querySelector('#email');
            const password = registerForm.querySelector('#password');
            let isValid = true;

            if (!username.value.trim()) {
                alert('Username is required.');
                isValid = false;
            }
             if (!email.value.trim()) { // Basic check, more robust validation needed for email format
                alert('Email is required.');
                isValid = false;
            }
            if (!password.value.trim()) {
                alert('Password is required.');
                isValid = false;
            }
            // Add more complex validation if needed (e.g., password strength)

            if (!isValid) {
                event.preventDefault(); // Stop form submission if invalid
            }
        });
    }

    // Example: Add interactivity to bid buttons (e.g., log item name)
    const bidButtons = document.querySelectorAll('.bid-button');
    bidButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            event.preventDefault(); // Prevent default link behavior
            const item = button.closest('.auction-item');
            const itemName = item.querySelector('h3').textContent;
            console.log(`Bid button clicked for: ${itemName}`);
            alert(`You clicked bid for: ${itemName}. Feature coming soon!`);
            // In a real app, this would likely open a modal or redirect to a bidding page
        });
    });
});

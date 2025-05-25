/* filepath: /Users/rajnandan1/Code/cman2/static/js/main.js */

// Wait for the document to be fully loaded
document.addEventListener("DOMContentLoaded", function () {
    // Handle the scroll count input in the index page
    const scrollCountInput = document.getElementById("scrollCount");
    if (scrollCountInput) {
        // Update the displayed value when the user changes the input
        scrollCountInput.addEventListener("input", function () {
            const value = parseInt(this.value, 10);
            if (value < 1) this.value = 1;
            if (value > 10) this.value = 10;
        });
    }

    // Add event listeners to tweets for highlighting on the tweets page
    const tweetCards = document.querySelectorAll(".tweet-card");
    tweetCards.forEach((card) => {
        card.addEventListener("click", function () {
            // Remove highlight from all cards
            tweetCards.forEach((c) => {
                c.classList.remove("selected");
                c.classList.remove("border-buttonBg");
                c.classList.remove("shadow-md");
                c.classList.add("border-gray-200");
            });
            // Add highlight to the clicked card
            this.classList.add("selected");
            this.classList.add("border-buttonBg");
            this.classList.add("shadow-md");
            this.classList.remove("border-gray-200");
        });
    });

    // Handle reply editing functionality
    const editReplyBtn = document.getElementById("editReplyBtn");
    const replyTextDisplay = document.getElementById("replyTextDisplay");
    const replyTextEditor = document.getElementById("replyTextEditor");
    const editorControls = document.getElementById("editorControls");
    const cancelEditBtn = document.getElementById("cancelEditBtn");
    const saveEditBtn = document.getElementById("saveEditBtn");
    const editedReplyInput = document.getElementById("editedReplyInput");

    if (editReplyBtn && replyTextDisplay && replyTextEditor && editorControls) {
        // Show editor when edit button is clicked
        editReplyBtn.addEventListener("click", function () {
            replyTextDisplay.classList.add("hidden");
            replyTextEditor.classList.remove("hidden");
            editorControls.classList.remove("hidden");
            editReplyBtn.classList.add("hidden");

            // Focus on the editor
            replyTextEditor.focus();
        });

        // Hide editor when cancel button is clicked
        if (cancelEditBtn) {
            cancelEditBtn.addEventListener("click", function () {
                replyTextEditor.value = replyTextDisplay.textContent.trim();
                replyTextDisplay.classList.remove("hidden");
                replyTextEditor.classList.add("hidden");
                editorControls.classList.add("hidden");
                editReplyBtn.classList.remove("hidden");
            });
        }

        // Save edited text when save button is clicked
        if (saveEditBtn && editedReplyInput) {
            saveEditBtn.addEventListener("click", function () {
                const editedText = replyTextEditor.value.trim();
                replyTextDisplay.textContent = editedText;
                editedReplyInput.value = editedText;

                replyTextDisplay.classList.remove("hidden");
                replyTextEditor.classList.add("hidden");
                editorControls.classList.add("hidden");
                editReplyBtn.classList.remove("hidden");
            });
        }
    }

    // Handle confirmation dialog for posting replies
    const confirmForm = document.getElementById("confirmForm");
    if (confirmForm) {
        confirmForm.addEventListener("submit", function (event) {
            const confirmValue = event.submitter.value;
            // Only validate checkbox if user is posting the reply (yes button)
            if (
                confirmValue === "yes" &&
                !document.getElementById("confirmCheckbox").checked
            ) {
                event.preventDefault();

                // Create a more stylish notification instead of using alert
                const notification = document.createElement("div");
                notification.className =
                    "fixed top-4 right-4 bg-red-50 text-red-700 px-4 py-3 rounded-md shadow-md border border-red-200 flex items-center space-x-2 z-50";
                notification.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                    </svg>
                    <span>Please confirm that you want to post this reply</span>
                `;

                document.body.appendChild(notification);

                // Remove the notification after 3 seconds
                setTimeout(() => {
                    notification.classList.add("opacity-0");
                    notification.style.transition = "opacity 0.5s ease";
                    setTimeout(() => notification.remove(), 500);
                }, 3000);
            }
        });
    }

    // Handle copy to clipboard functionality for the generated reply
    const copyReplyBtn = document.getElementById("copyReplyBtn");
    if (copyReplyBtn) {
        copyReplyBtn.addEventListener("click", function () {
            const replyText =
                document.getElementById("generatedReply").textContent;
            navigator.clipboard
                .writeText(replyText)
                .then(function () {
                    // Change button text temporarily
                    const originalText = copyReplyBtn.textContent;
                    copyReplyBtn.textContent = "Copied!";
                    setTimeout(() => {
                        copyReplyBtn.textContent = originalText;
                    }, 2000);
                })
                .catch(function (err) {
                    console.error("Could not copy text: ", err);
                });
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach((alert) => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Initialize tooltips if Bootstrap is loaded
    if (typeof bootstrap !== "undefined" && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(
            document.querySelectorAll('[data-toggle="tooltip"]')
        );
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});

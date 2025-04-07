// Handle form submissions
document.addEventListener('DOMContentLoaded', function() {
    // Handle new message form submission
    const newMessageForm = document.querySelector('#newMessageModal form');
    if (newMessageForm) {
        newMessageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const recipientId = this.querySelector('#recipient').value;
            const content = this.querySelector('textarea[name="content"]').value;
            
            // Redirect to the chat with the selected user
            window.location.href = `/messages?user_id=${recipientId}`;
        });
    }

    // Handle avatar upload preview
    const avatarInput = document.querySelector('input[type="file"][name="avatar"]');
    if (avatarInput) {
        avatarInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.querySelector('.avatar-preview img');
                    if (preview) {
                        preview.src = e.target.result;
                    }
                }
                reader.readAsDataURL(file);
            }
        });
    }

    // Handle delete account confirmation
    const deleteAccountBtn = document.querySelector('.delete-account-btn');
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    }

    // Handle logout confirmation
    const logoutBtn = document.querySelector('.logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to logout?')) {
                e.preventDefault();
            }
        });
    }

    // Handle connection request actions
    const acceptRequestBtns = document.querySelectorAll('.accept-request-btn');
    acceptRequestBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to accept this connection request?')) {
                e.preventDefault();
            }
        });
    });

    const rejectRequestBtns = document.querySelectorAll('.reject-request-btn');
    rejectRequestBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to reject this connection request?')) {
                e.preventDefault();
            }
        });
    });

    // Handle event registration
    const registerEventBtns = document.querySelectorAll('.register-event-btn');
    registerEventBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to register for this event?')) {
                e.preventDefault();
            }
        });
    });

    // Handle job application
    const applyJobBtns = document.querySelectorAll('.apply-job-btn');
    applyJobBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to apply for this job?')) {
                e.preventDefault();
            }
        });
    });

    // Handle user status toggle
    const toggleStatusBtns = document.querySelectorAll('.toggle-status-btn');
    toggleStatusBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const action = this.dataset.action;
            const username = this.dataset.username;
            if (!confirm(`Are you sure you want to ${action} user ${username}?`)) {
                e.preventDefault();
            }
        });
    });

    // Handle user deletion
    const deleteUserBtns = document.querySelectorAll('.delete-user-btn');
    deleteUserBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const username = this.dataset.username;
            if (!confirm(`Are you sure you want to delete user ${username}? This action cannot be undone.`)) {
                e.preventDefault();
            }
        });
    });
}); 
// Login 

async function login() {
    const username = document.getElementById('usernameInput').value.trim();
    const password = document.getElementById('passwordInput').value.trim();
    
    if (!username || !password) {
        alert('Please enter username and password');
        return;
    }
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentUsername = username;
            document.getElementById('userName').textContent = username;
            document.getElementById('userAvatar').textContent = username.charAt(0).toUpperCase();
            document.getElementById('loginModal').classList.add('hidden');
            await loadSession();
        } else {
            alert(data.error || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed. Please try again.');
    }
}

async function logout() {
    if (confirm('Are you sure you want to logout?')) {
        try {
            await fetch('/api/logout', {method: 'POST'});
            location.reload();
        } catch (error) {
            console.error('Logout error:', error);
            location.reload();
        }
    }
}

function toggleUserMenu() {
    const menu = document.getElementById('userMenu');
    menu.classList.toggle('hidden');
}

async function uploadProfilePhoto() {
    const input = document.getElementById('profilePhotoInput');
    const file = input.files[0];
    
    if (!file) {
        alert('Please select a photo');
        return;
    }
    
    const formData = new FormData();
    formData.append('photo', file);
    
    try {
        const response = await fetch('/api/profile-photo', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            const avatar = document.getElementById('userAvatar');
            avatar.innerHTML = `<img src="${data.photoUrl}?t=${Date.now()}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%; cursor: pointer;">`;
            alert('Profile photo updated!');
            input.value = '';
        } else {
            alert(data.error || 'Failed to upload photo');
        }
    } catch (error) {
        console.error('Upload photo error:', error);
        alert('Failed to upload photo. Please try again.');
    }
}

async function loadProfilePhoto() {
    try {
        const response = await fetch('/api/profile-photo');
        const data = await response.json();
        
        if (data.photoUrl) {
            const avatar = document.getElementById('userAvatar');
            avatar.innerHTML = `<img src="${data.photoUrl}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%; cursor: pointer;">`;
        }
    } catch (error) {
        console.error('Load photo error:', error);
    }
}

async function saveNutritionProfile() {
    const dietary = [];
    if (document.getElementById('vegan').checked) dietary.push('vegan');
    if (document.getElementById('vegetarian').checked) dietary.push('vegetarian');
    if (document.getElementById('glutenFree').checked) dietary.push('gluten-free');
    if (document.getElementById('dairyFree').checked) dietary.push('dairy-free');
    if (document.getElementById('nutFree').checked) dietary.push('nut-free');
    
    const profile = {
        dietary,
        healthGoal: document.getElementById('healthGoal').value,
        allergies: document.getElementById('allergies').value.split(',').map(a => a.trim()).filter(a => a)
    };
    
    try {
        const response = await fetch('/api/nutrition-profile', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(profile)
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Nutrition profile saved!');
        } else {
            alert(data.error || 'Failed to save profile');
        }
    } catch (error) {
        console.error('Save profile error:', error);
        alert('Failed to save profile');
    }
}

async function loadNutritionProfile() {
    try {
        const response = await fetch('/api/nutrition-profile');
        const data = await response.json();
        
        if (data.profile) {
            const p = data.profile;
            if (p.dietary) {
                document.getElementById('vegan').checked = p.dietary.includes('vegan');
                document.getElementById('vegetarian').checked = p.dietary.includes('vegetarian');
                document.getElementById('glutenFree').checked = p.dietary.includes('gluten-free');
                document.getElementById('dairyFree').checked = p.dietary.includes('dairy-free');
                document.getElementById('nutFree').checked = p.dietary.includes('nut-free');
            }
            if (p.healthGoal) document.getElementById('healthGoal').value = p.healthGoal;
            if (p.allergies) document.getElementById('allergies').value = p.allergies.join(', ');
        }
    } catch (error) {
        console.error('Load profile error:', error);
    }
}

function openSettings() {
    document.getElementById('userMenu').classList.add('hidden');
    document.getElementById('settingsModal').classList.remove('hidden');
    loadNutritionProfile();
    loadFavorites();
}

function closeSettings() {
    document.getElementById('settingsModal').classList.add('hidden');
    document.getElementById('currentPassword').value = '';
    document.getElementById('newPassword').value = '';
    document.getElementById('confirmPassword').value = '';
}

async function changePassword() {
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (!currentPassword || !newPassword || !confirmPassword) {
        alert('Please fill in all password fields');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        alert('New passwords do not match');
        return;
    }
    
    if (newPassword.length < 6) {
        alert('Password must be at least 6 characters');
        return;
    }
    
    try {
        const response = await fetch('/api/change-password', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({currentPassword, newPassword})
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Password changed successfully!');
            closeSettings();
        } else {
            alert(data.error || 'Failed to change password');
        }
    } catch (error) {
        console.error('Change password error:', error);
        alert('Failed to change password');
    }
}

async function clearChatHistory() {
    if (confirm('Are you sure? This will permanently delete all your chats.')) {
        try {
            const response = await fetch('/api/clear-chats', {method: 'POST'});
            const data = await response.json();
            
            if (data.success) {
                alert('Chat history cleared!');
                closeSettings();
                location.reload();
            } else {
                alert(data.error || 'Failed to clear chats');
            }
        } catch (error) {
            console.error('Clear chats error:', error);
            alert('Failed to clear chats');
        }
    }
}

async function clearUploadedFiles() {
    if (confirm('Are you sure? This will permanently delete all your uploaded files.')) {
        try {
            const response = await fetch('/api/clear-files', {method: 'POST'});
            const data = await response.json();
            
            if (data.success) {
                alert('Uploaded files cleared!');
                closeSettings();
                location.reload();
            } else {
                alert(data.error || 'Failed to clear files');
            }
        } catch (error) {
            console.error('Clear files error:', error);
            alert('Failed to clear files');
        }
    }
}

function handleLoginKeyPress(event) {
    if (event.key === 'Enter') login();
}

async function loadSession() {
    try {
        const response = await fetch('/api/session');
        const data = await response.json();
        
        if (data.username) {
            currentUsername = data.username;
            document.getElementById('userName').textContent = data.username;
            document.getElementById('userAvatar').textContent = data.username.charAt(0).toUpperCase();
            document.getElementById('loginModal').classList.add('hidden');
            await loadProfilePhoto();
        } else {
            document.getElementById('loginModal').classList.remove('hidden');
        }
        
        // Render chat list
        if (typeof renderChatList === 'function' && data.chats) {
            renderChatList(data.chats);
        }
        
        // Load current chat if exists
        if (data.current_chat && typeof loadChat === 'function') {
            loadChat(data.current_chat);
        }
    } catch (error) {
        console.error('Load session error:', error);
        document.getElementById('loginModal').classList.remove('hidden');
    }
}

// Add click handler to avatar on page load
document.addEventListener('DOMContentLoaded', () => {
    const avatar = document.getElementById('userAvatar');
    if (avatar) avatar.addEventListener('click', toggleUserMenu);
});

// Close menu when clicking outside
document.addEventListener('click', (e) => {
    const menu = document.getElementById('userMenu');
    const avatar = document.getElementById('userAvatar');
    if (menu && !menu.classList.contains('hidden') && !menu.contains(e.target) && e.target !== avatar && !avatar.contains(e.target)) {
        menu.classList.add('hidden');
    }
});
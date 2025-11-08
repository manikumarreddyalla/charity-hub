// frontend/js/app.js
const API_BASE = '/api'; // same origin - Flask serves frontend

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('ngoList')) loadNGOs();
  if (document.getElementById('ngoSelect')) populateNGOSelect();
  if (document.getElementById('donationForm')) document.getElementById('donationForm').addEventListener('submit', submitDonation);
  if (document.getElementById('donationChart')) loadDashboard();

  // Login/Register pages
  if (document.getElementById('loginForm')) document.getElementById('loginForm').addEventListener('submit', login);
  if (document.getElementById('registerForm')) document.getElementById('registerForm').addEventListener('submit', register);
});

async function fetchJSON(path, opts = {}) {
  try {
    const res = await fetch(API_BASE + path, opts);
    return await res.json();
  } catch (e) {
    console.error('API error', e);
    return null;
  }
}

// ========== AUTH ==========
async function login(e) {
  e.preventDefault();
  const email = document.getElementById('loginEmail').value;
  const password = document.getElementById('loginPassword').value;
  const msg = document.getElementById('loginMsg');

  const res = await fetchJSON('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });

  if (res && res.success) {
    localStorage.setItem('csp_token', res.token);
    msg.textContent = 'Login successful!';
    msg.style.background = '#e6ffef';
    setTimeout(() => (window.location.href = '/dashboard.html'), 700);
  } else {
    msg.textContent = res && res.error ? res.error : 'Login failed';
    msg.style.background = '#ffe6e6';
  }
}

async function register(e) {
  e.preventDefault();
  const name = document.getElementById('regName').value;
  const email = document.getElementById('regEmail').value;
  const password = document.getElementById('regPassword').value;
  const msg = document.getElementById('regMsg');

  const res = await fetchJSON('/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password })
  });

  if (res && res.success) {
    localStorage.setItem('csp_token', res.token);
    msg.textContent = 'Registered successfully!';
    msg.style.background = '#e6ffef';
    setTimeout(() => (window.location.href = '/dashboard.html'), 700);
  } else {
    msg.textContent = res && res.error ? res.error : 'Registration failed';
    msg.style.background = '#ffe6e6';
  }
}

// ========== NGO LIST ==========
async function loadNGOs() {
  const data = await fetchJSON('/ngos');
  const root = document.getElementById('ngoList');
  root.innerHTML = '';
  if (!data || !Array.isArray(data)) return (root.innerHTML = '<p>Failed to load NGOs.</p>');
  data.forEach(n => {
    const div = document.createElement('div');
    div.className = 'card';
    div.innerHTML = `<h3>${n.name}</h3><p>${n.location} • ${n.category}</p><p>${n.summary}</p>`;
    root.appendChild(div);
  });
}

async function populateNGOSelect() {
  const data = await fetchJSON('/ngos');
  const sel = document.getElementById('ngoSelect');
  sel.innerHTML = '<option value="">Select an NGO</option>';
  data.forEach(n => {
    const opt = document.createElement('option');
    opt.value = n.id;
    opt.textContent = `${n.name} — ${n.location}`;
    sel.appendChild(opt);
  });
}

// ========== DONATION ==========
async function submitDonation(e) {
  e.preventDefault();
  const name = document.getElementById('donorName').value;
  const email = document.getElementById('donorEmail').value;
  const ngo_id = document.getElementById('ngoSelect').value;
  const amount = Number(document.getElementById('amount').value);
  const msgEl = document.getElementById('donationMsg');
  msgEl.textContent = 'Processing...';

  const res = await fetchJSON('/donate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, ngo_id, amount })
  });

  if (res && res.success) {
    msgEl.innerHTML = `Thanks! Donation recorded. <a href="${res.receipt_url}" target="_blank">Download receipt</a>`;
    msgEl.style.background = '#e6ffef';
  } else {
    msgEl.textContent = 'Failed to process donation.';
    msgEl.style.background = '#ffe6e6';
  }
}

// ========== DASHBOARD ==========
async function loadDashboard() {
  const data = await fetchJSON('/dashboard');
  if (!data) return;
  const ctx = document.getElementById('donationChart').getContext('2d');
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.by_ngo.map(x => x.name),
      datasets: [{ label: 'Total donations', data: data.by_ngo.map(x => x.total) }]
    },
    options: { responsive: true }
  });
}

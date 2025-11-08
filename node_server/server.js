const express = require('express');
const path = require('path');
const cors = require('cors');

const app = express();
app.use(cors());
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname, '../frontend')));

// fallback to index
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/index.html'));
});

app.listen(PORT, () => console.log(`Frontend server running on http://localhost:${PORT}`));

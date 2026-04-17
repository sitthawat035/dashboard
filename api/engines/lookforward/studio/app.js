const API_BASE = "http://127.0.0.1:5000/api";

document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const navItems = document.querySelectorAll('.nav-item');
    const views = document.querySelectorAll('.content-view');
    const megaIgniteBtn = document.getElementById('mega-ignite-btn');
    const quickIgniteBtn = document.getElementById('quick-ignite');
    const topicInput = document.getElementById('topic-input');
    const loadingOverlay = document.getElementById('loading-overlay');
    const procStatus = document.getElementById('proc-status');
    const previewModal = document.getElementById('preview-modal');

    // View Management
    function switchView(viewId) {
        views.forEach(v => v.classList.remove('active'));
        navItems.forEach(n => n.classList.remove('active'));

        const targetView = document.getElementById(`${viewId}-view`);
        if (targetView) targetView.classList.add('active');

        const activeNavItem = document.querySelector(`.nav-item[data-view="${viewId}"]`);
        if (activeNavItem) activeNavItem.classList.add('active');

        if (viewId === 'dashboard') loadDashboardV2();
    }

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            switchView(item.dataset.view);
        });
    });

    if (megaIgniteBtn) {
        megaIgniteBtn.addEventListener('click', () => switchView('generator'));
    }

    if (quickIgniteBtn) {
        quickIgniteBtn.addEventListener('click', () => switchView('generator'));
    }

    const backBtn = document.querySelector('.btn-back');
    if (backBtn) {
        backBtn.addEventListener('click', () => switchView('dashboard'));
    }

    // Dashboard V2 Data Loading
    async function loadDashboardV2() {
        try {
            const response = await fetch(`${API_BASE}/posts`);
            const posts = await response.json();

            const listContainer = document.querySelector('.v2-list');
            if (!listContainer) return;

            listContainer.innerHTML = '';

            if (posts.length === 0) {
                listContainer.innerHTML = '<p style="padding: 20px; color: var(--text-dim); text-align: center;">Neural vault is empty.<br>Ignite an analysis to begin.</p>';
                updateGauge(0);
                return;
            }

            let totalScore = 0;
            posts.forEach(post => {
                const scoreValue = parseFloat(post.score);
                if (!isNaN(scoreValue)) totalScore += scoreValue;

                const item = document.createElement('div');
                item.className = 'v2-post-item';
                item.innerHTML = `
                    <div class="v2-item-icon">
                        <i class="fa-solid fa-microchip"></i>
                    </div>
                    <div class="post-info">
                        <h4>${post.topic}</h4>
                        <p>${post.date} • Insight ID: ${post.id.substring(0, 8).toUpperCase()}</p>
                    </div>
                    <div class="post-actions" style="margin-left: auto;">
                        <button class="btn-icon btn-preview" data-id="${post.id}" data-date="${post.date}" title="Preview Feed" style="border:none; background:transparent; color:var(--primary-cyan); cursor:pointer; font-size:18px;">
                            <i class="fa-solid fa-eye"></i>
                        </button>
                    </div>
                `;
                listContainer.appendChild(item);
            });

            const avgScore = posts.length > 0 ? (totalScore / posts.length).toFixed(1) : 0;
            updateGauge(avgScore);

            // Add event listeners for preview buttons
            document.querySelectorAll('.btn-preview').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    showPreview(btn.dataset.date, btn.dataset.id);
                });
            });
        } catch (err) {
            console.error("Neural sync failure:", err);
            const listContainer = document.querySelector('.v2-list');
            if (listContainer) listContainer.innerHTML = '<p style="color: #ff4444; padding: 20px;">FAILED TO SYNC WITH VAULT</p>';
        }
    }

    // Gauge Animation
    function updateGauge(score) {
        const gaugeFill = document.getElementById('gauge-fill');
        const gaugeValue = document.getElementById('gauge-value');
        const needle = document.querySelector('.gauge-needle');

        if (!gaugeFill || !gaugeValue || !needle) return;

        // Score 0-5 mapping to dashoffset (251.2 is 0%, 0 is 100% of half circle)
        const scoreNum = Math.min(5, Math.max(0, parseFloat(score)));
        const percentage = scoreNum / 5;
        const offset = 251.2 * (1 - percentage);

        gaugeFill.style.strokeDashoffset = offset;
        gaugeValue.innerText = scoreNum;

        // Needle rotation: -90deg to 90deg
        const rotation = (percentage * 180) - 90;
        needle.style.transform = `rotate(${rotation}deg)`;
    }

    // Preview Logic
    const closeBtns = document.querySelectorAll('.btn-close-modal, .btn-close-modal-bottom');

    async function showPreview(date, id) {
        try {
            const response = await fetch(`${API_BASE}/posts/${date}/${id}`);
            if (!response.ok) throw new Error("Post not found");
            const data = await response.json();

            document.getElementById('preview-date').innerText = `${data.date} • 🌐`;
            document.getElementById('preview-body').innerText = data.body || "No content found.";
            document.getElementById('preview-caption').innerText = (data.caption || "").trim();
            document.getElementById('preview-hashtags').innerText = (data.hashtags || "").trim();

            const mediaContainer = document.getElementById('preview-media');
            mediaContainer.innerHTML = '';
            if (data.images && data.images.length > 0) {
                data.images.forEach(url => {
                    const img = document.createElement('img');
                    img.src = url;
                    mediaContainer.appendChild(img);
                });
            } else {
                mediaContainer.innerHTML = '<div style="color: #65676b; padding: 40px; text-align: center;"><i class="fa-regular fa-image" style="font-size: 3rem; display: block; margin-bottom: 10px;"></i>No media generated</div>';
            }

            previewModal.classList.remove('hidden');
        } catch (err) {
            alert("Neural access error: " + err.message);
        }
    }

    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => previewModal.classList.add('hidden'));
    });

    // Copy Content Logic
    const copyAllBtn = document.querySelector('.btn-copy-all');
    if (copyAllBtn) {
        copyAllBtn.addEventListener('click', () => {
            const body = document.getElementById('preview-body').innerText;
            const caption = document.getElementById('preview-caption').innerText;
            const hashtags = document.getElementById('preview-hashtags').innerText;

            const fullText = `${body}\n\n---\n\n${caption}\n\n${hashtags}`;
            navigator.clipboard.writeText(fullText).then(() => {
                const originalText = copyAllBtn.innerText;
                copyAllBtn.innerText = "✅ COPIED";
                setTimeout(() => copyAllBtn.innerText = originalText, 2000);
            });
        });
    }

    // Ignite Action (Generator)
    const igniteBtn = document.getElementById('ignite-btn');
    if (igniteBtn) {
        igniteBtn.addEventListener('click', async () => {
            const topic = topicInput.value.trim();
            if (!topic) {
                topicInput.style.borderColor = 'var(--primary-cyan)';
                setTimeout(() => { topicInput.style.borderColor = 'rgba(255,255,255,0.08)'; }, 1000);
                return;
            }

            loadingOverlay.classList.remove('hidden');
            procStatus.innerText = "Initializing Authority Core...";

            // Safety timeout: 45 seconds
            const safetyTimeout = setTimeout(() => {
                if (!loadingOverlay.classList.contains('hidden')) {
                    loadingOverlay.classList.add('hidden');
                    console.warn("IGNITION TIMEOUT: Overlay cleared by safety watchdog.");
                }
            }, 45000);

            try {
                const response = await fetch(`${API_BASE}/ignite`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ topic })
                });

                const result = await response.json();
                if (result.status === 'success') {
                    procStatus.innerText = "SUCCESS: Analysis Complete";
                    setTimeout(() => {
                        loadingOverlay.classList.add('hidden');
                        topicInput.value = '';
                        loadDashboardV2();
                        switchView('dashboard');
                    }, 1500);
                } else {
                    throw new Error(result.error || result.message);
                }
            } catch (err) {
                loadingOverlay.classList.add('hidden');
                console.error("Neural linkage error:", err);
                alert(`IGNITION FAILURE: ${err.message}`);
            } finally {
                clearTimeout(safetyTimeout);
            }
        });
    }

    // Initial Load
    loadDashboardV2();
    console.log("lookforward V2: Neural Link Established.");
});

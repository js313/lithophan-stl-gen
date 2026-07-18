// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const uploadPrompt = document.getElementById('upload-prompt');
const previewContainer = document.getElementById('preview-container');
const imagePreview = document.getElementById('image-preview');
const removeImgBtn = document.getElementById('remove-img-btn');

const generatorForm = document.getElementById('generator-form');
const generateBtn = document.getElementById('generate-btn');

const minThicknessInput = document.getElementById('min-thickness');
const minThicknessVal = document.getElementById('min-thickness-val');
const maxThicknessInput = document.getElementById('max-thickness');
const maxThicknessVal = document.getElementById('max-thickness-val');
const maxSideInput = document.getElementById('max-side');
const maxSideVal = document.getElementById('max-side-val');

const canvasContainer = document.getElementById('canvas-container');
const viewportPlaceholder = document.getElementById('viewport-placeholder');
const viewportLoading = document.getElementById('viewport-loading');
const viewportControls = document.getElementById('viewport-controls');
const resetViewBtn = document.getElementById('reset-view-btn');
const toggleWireframeBtn = document.getElementById('toggle-wireframe-btn');

const downloadActions = document.getElementById('download-actions');
const downloadBtn = document.getElementById('download-btn');
const meshTriangles = document.getElementById('mesh-triangles');
const meshDimensions = document.getElementById('mesh-dimensions');

// Three.js Global Variables
let scene, camera, renderer, controls, currentMesh;
let isThreeInitialized = false;

// 1. Parameter display updates
minThicknessInput.addEventListener('input', (e) => {
    minThicknessVal.textContent = `${e.target.value} mm`;
    // Validate: min cannot be greater than max
    if (parseFloat(minThicknessInput.value) > parseFloat(maxThicknessInput.value)) {
        maxThicknessInput.value = minThicknessInput.value;
        maxThicknessVal.textContent = `${minThicknessInput.value} mm`;
    }
});

maxThicknessInput.addEventListener('input', (e) => {
    maxThicknessVal.textContent = `${e.target.value} mm`;
    // Validate: max cannot be less than min
    if (parseFloat(maxThicknessInput.value) < parseFloat(minThicknessInput.value)) {
        minThicknessInput.value = maxThicknessInput.value;
        minThicknessVal.textContent = `${maxThicknessInput.value} mm`;
    }
});

maxSideInput.addEventListener('input', (e) => {
    maxSideVal.textContent = `${e.target.value} mm`;
});

// 2. Drag & Drop Upload Zone Handler
dropZone.addEventListener('click', (e) => {
    // Only trigger file picker if clicking prompt (not the remove button)
    if (!e.target.closest('#remove-img-btn')) {
        fileInput.click();
    }
});

// Drag events
['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    }, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
    }, false);
});

dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0 && files[0].type.startsWith('image/')) {
        fileInput.files = files;
        handleFileSelect(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

function handleFileSelect(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        uploadPrompt.style.display = 'none';
        previewContainer.style.display = 'flex';
        generateBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}

removeImgBtn.addEventListener('click', (e) => {
    e.stopPropagation(); // Prevent file input click trigger
    fileInput.value = '';
    imagePreview.src = '';
    previewContainer.style.display = 'none';
    uploadPrompt.style.display = 'flex';
    generateBtn.disabled = true;
    
    // Hide download actions if any
    downloadActions.style.display = 'none';
    
    // Reset viewport to placeholder
    if (currentMesh) {
        scene.remove(currentMesh);
        currentMesh = null;
    }
    viewportControls.style.display = 'none';
    viewportPlaceholder.style.display = 'flex';
});

// 3. API Submission & STL Generation
generatorForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!fileInput.files[0]) return;

    // Show Loading
    viewportPlaceholder.style.display = 'none';
    viewportLoading.style.display = 'flex';
    viewportControls.style.display = 'none';
    downloadActions.style.display = 'none';
    
    // Disable inputs while generating
    generateBtn.disabled = true;
    const inputs = generatorForm.querySelectorAll('input, button');
    inputs.forEach(el => el.disabled = true);

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('min_thickness', minThicknessInput.value);
    formData.append('max_thickness', maxThicknessInput.value);
    formData.append('max_side', maxSideInput.value);

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            let errorMessage = "An error occurred during STL generation.";
            try {
                const errorJson = JSON.parse(errorText);
                errorMessage = errorJson.detail || errorMessage;
            } catch (pErr) {}
            throw new Error(errorMessage);
        }

        const stlBlob = await response.blob();
        
        // Setup download link
        const downloadUrl = URL.createObjectURL(stlBlob);
        downloadBtn.href = downloadUrl;
        downloadBtn.download = `${fileInput.files[0].name.split('.')[0]}_lithophane.stl`;
        
        // Render in 3D
        await loadSTLToViewport(stlBlob);
        
        // Show Download actions
        downloadActions.style.display = 'flex';
        viewportControls.style.display = 'flex';

    } catch (err) {
        console.error(err);
        alert(`Error: ${err.message}`);
        viewportPlaceholder.style.display = 'flex';
    } finally {
        // Re-enable inputs
        viewportLoading.style.display = 'none';
        inputs.forEach(el => el.disabled = false);
        // keep remove button enabled
        removeImgBtn.disabled = false;
    }
});

// 4. Three.js Renderer Setup
function initThree() {
    const width = canvasContainer.clientWidth;
    const height = canvasContainer.clientHeight;

    // Scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x06090f);

    // Camera
    camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    // Z is up for STL files generated by standard 3D apps
    camera.up.set(0, 0, 1);
    camera.position.set(0, -200, 150);

    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    
    // Clear any previous canvas element
    const existingCanvas = canvasContainer.querySelector('canvas');
    if (existingCanvas) {
        existingCanvas.remove();
    }
    
    canvasContainer.appendChild(renderer.domElement);

    // Controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 + 0.1; // Limit panning under base

    // Lights
    const ambientLight = new THREE.AmbientLight(0x666666);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight1.position.set(100, 100, 200);
    dirLight1.castShadow = true;
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0xfff3e0, 0.4); // soft yellow backlighting
    dirLight2.position.set(-100, -100, -50);
    scene.add(dirLight2);

    // Animation Loop
    function animate() {
        requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera);
    }
    animate();

    // Window Resize Handler
    window.addEventListener('resize', () => {
        if (!canvasContainer) return;
        const w = canvasContainer.clientWidth;
        const h = canvasContainer.clientHeight;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
    });

    isThreeInitialized = true;
}

// 5. Load and display STL file
async function loadSTLToViewport(blob) {
    if (!isThreeInitialized) {
        initThree();
    }

    if (currentMesh) {
        scene.remove(currentMesh);
    }

    const reader = new FileReader();
    
    return new Promise((resolve) => {
        reader.onload = function (e) {
            const contents = e.target.result;
            const loader = new THREE.STLLoader();
            const geometry = loader.parse(contents);
            
            // Materials: Ivory Matte PLA filament style
            const material = new THREE.MeshStandardMaterial({
                color: 0xf3f2eb,
                roughness: 0.65,
                metalness: 0.05,
                side: THREE.DoubleSide
            });
            
            currentMesh = new THREE.Mesh(geometry, material);
            currentMesh.castShadow = true;
            currentMesh.receiveShadow = true;
            
            // Center the geometry
            geometry.center();
            
            scene.add(currentMesh);

            // Compute statistics
            geometry.computeBoundingBox();
            const size = new THREE.Vector3();
            geometry.boundingBox.getSize(size);
            
            const numTriangles = geometry.attributes.position.count / 3;
            
            meshTriangles.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> ${numTriangles.toLocaleString()} polygons`;
            meshDimensions.innerHTML = `<i class="fa-solid fa-maximize"></i> ${size.x.toFixed(1)} x ${size.y.toFixed(1)} x ${size.z.toFixed(1)} mm`;

            // Adjust camera to fit the mesh size
            geometry.computeBoundingSphere();
            const sphere = geometry.boundingSphere;
            const radius = sphere.radius;
            
            // Reposition camera cleanly
            camera.position.set(0, -radius * 2.0, radius * 1.5);
            controls.target.set(0, 0, 0);
            controls.update();

            resolve();
        };
        
        reader.readAsArrayBuffer(blob);
    });
}

// 6. Viewport button handlers
resetViewBtn.addEventListener('click', () => {
    if (!currentMesh) return;
    currentMesh.geometry.computeBoundingSphere();
    const sphere = currentMesh.geometry.boundingSphere;
    const radius = sphere.radius;
    camera.position.set(0, -radius * 2.0, radius * 1.5);
    controls.target.set(0, 0, 0);
    controls.update();
});

toggleWireframeBtn.addEventListener('click', () => {
    if (!currentMesh) return;
    const isWire = currentMesh.material.wireframe;
    currentMesh.material.wireframe = !isWire;
    
    // Toggle active state styling if desired
    toggleWireframeBtn.style.background = !isWire ? 'var(--accent)' : 'rgba(17, 25, 40, 0.6)';
    toggleWireframeBtn.style.borderColor = !isWire ? 'var(--accent)' : 'rgba(255, 255, 255, 0.1)';
});

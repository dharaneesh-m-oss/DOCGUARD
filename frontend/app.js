document.addEventListener('DOMContentLoaded', () => {
    const specZone = document.getElementById('spec-zone');
    const photoZone = document.getElementById('photo-zone');
    const specInput = document.getElementById('spec-file');
    const photoInput = document.getElementById('photo-file');
    const specName = document.getElementById('spec-name');
    const photoName = document.getElementById('photo-name');
    const processBtn = document.getElementById('process-btn');
    const statusPanel = document.getElementById('status-panel');
    const loadingState = document.getElementById('loading-state');
    const resultState = document.getElementById('result-state');
    const resultText = document.getElementById('result-text');
    const downloadBtn = document.getElementById('download-btn');

    let files = {
        spec: null,
        photo: null
    };

    // Setup Zones
    [
        { zone: specZone, input: specInput, key: 'spec', label: specName },
        { zone: photoZone, input: photoInput, key: 'photo', label: photoName }
    ].forEach(({ zone, input, key, label }) => {
        zone.addEventListener('click', () => input.click());
        
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('active');
        });

        zone.addEventListener('dragleave', () => zone.classList.remove('active'));

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('active');
            if (e.dataTransfer.files.length) {
                handleFileSelect(e.dataTransfer.files[0], key, label);
            }
        });

        input.addEventListener('change', (e) => {
            if (e.target.files.length) {
                handleFileSelect(e.target.files[0], key, label);
            }
        });
    });

    function handleFileSelect(file, key, labelEl) {
        files[key] = file;
        labelEl.textContent = file.name;
        checkReady();
    }

    function checkReady() {
        processBtn.disabled = !(files.spec && files.photo);
    }

    // Process Action
    processBtn.addEventListener('click', async () => {
        statusPanel.style.display = 'block';
        loadingState.style.display = 'block';
        resultState.style.display = 'none';
        processBtn.disabled = true;

        const formData = new FormData();
        formData.append('spec_file', files.spec);
        formData.append('photo_file', files.photo);

        try {
            const response = await fetch('http://127.0.0.1:8000/update-doc', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            loadingState.style.display = 'none';
            resultState.style.display = 'block';

            if (data.success) {
                resultText.textContent = 'Synthesis Complete. Your document is ready.';
                resultText.style.color = '#fff';
                // Backend output path is 'audit_out/updated_template.docx'
                // For direct download, we'll need a static mount or a proxy
                // For now, pointing to the path provided
                downloadBtn.href = `http://127.0.0.1:8000/${data.output_path}`;
                downloadBtn.style.display = 'inline-block';
            } else {
                resultText.textContent = `Processing Failed: ${data.message}`;
                resultText.style.color = '#ff453a';
                downloadBtn.style.display = 'none';
            }
        } catch (error) {
            loadingState.style.display = 'none';
            resultState.style.display = 'block';
            resultText.textContent = `Connection Error: ${error.message}`;
            resultText.style.color = '#ff453a';
        } finally {
            processBtn.disabled = false;
        }
    });
});

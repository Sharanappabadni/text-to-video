function sendGeneratePrompt() {
    const prompt = document.getElementById("userInput").value;
    const user_email = document.getElementById("user-email").value;
    document.getElementById("userInput").value = ""; // Clear the input field

    // Append the user's prompt to the chat messages container
    appendYouMessage(prompt);

    const requestBody = {
        "user_email": user_email,
        "prompt": prompt,
        "action": "generate"
    };

    sendPromptRequest(requestBody);
}
function appendYouMessage(message) {
    appendMessage("You: " + message, "user");
}

function appendAgentMessage(message) {
    appendMessage("Agent: " + message, "agent");
}

function sendRetrievePrompt() {
    const userData = JSON.parse(localStorage.getItem('loginData'));
    const prompt = document.getElementById("userInput").value;
    document.getElementById("userInput").value = ""; // Clear the input field

    // Append the user's prompt to the chat messages container
    appendYouMessage(prompt);
    console.log("prompt is "+prompt)
    console.log("user email is "+userData.email)

    const requestBody = {
        "user_email": userData.email,
        "prompt": prompt,
        "action": "retrieve"
    };
    sendPromptRequest(requestBody);
}

function sendPromptRequest(requestBody) {
    // Send a POST request to the specified endpoint (localhost:9000/get_response)
    fetch('http://localhost:9000/get_response', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === "Video generated" || data.message === "Matching video found") {
            if (data.video_url) {
                // Append the video player within the chat
                appendVideo(data.video_url);
            } else {
                document.getElementById("videoInfo").innerText = ""; // Clear video info
                document.getElementById("videoPlayer").src = ""; // Clear video player
            }
        } else {
            // Display an error message
            appendAgentMessage("Error: " + data.detail, "agent");
            document.getElementById("videoInfo").innerText = ""; // Clear video info
            document.getElementById("videoPlayer").src = ""; // Clear video player
        }
    })
    .catch(error => console.error(error));
}

function appendMessage(message, sender) {
    const chatMessages = document.getElementById("chatMessages");
    const messageDiv = document.createElement("div");

    if (sender === "user") {
        messageDiv.className = "user-message";
    } else if (sender === "agent") {
        messageDiv.className = "agent-message";
    }

    messageDiv.innerText = message;
    chatMessages.appendChild(messageDiv);

    // Scroll to the bottom of the chat messages container to show the latest messages
    chatMessages.scrollTop = chatMessages.scrollHeight;
}


function appendVideo(videoUrl) {
    const chatMessages = document.getElementById("chatMessages");

    // Create a container div for the agent's message
    const agentMessageDiv = document.createElement("div");
    agentMessageDiv.className = "agent-message"; // Style for agent message

    // Create an "Agent:" label
    const agentLabel = document.createElement("div");
    agentLabel.innerText = "Agent:";
    agentLabel.className = "agent-label"; // Style for the agent label

    // Create the video iframe
    const video = document.createElement("iframe");
    const parts = videoUrl.split("dreams/");
    const textAfterDreams = parts[1];
    console.log(textAfterDreams);

    video.setAttribute("src", `http://localhost:10000/${textAfterDreams}`);
    video.setAttribute("width", "640");
    video.setAttribute("height", "440");
    video.setAttribute("frameborder", "0");

    // Append the "Agent:" label and video to the agent's message container
    agentMessageDiv.appendChild(agentLabel);
    agentMessageDiv.appendChild(video);

    // Append the agent's message container to the chat messages container
    chatMessages.appendChild(agentMessageDiv);

    // Scroll to the bottom of the chat messages container to show the latest messages
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

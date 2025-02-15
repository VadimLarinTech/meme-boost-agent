import React, { useEffect, useState } from "react";

function TweetsPage() {
    const [tweets, setTweets] = useState([]);
    const [generatedTweet, setGeneratedTweet] = useState("");
    const [image, setImage] = useState(null);
    const [isLoadingTweet, setIsLoadingTweet] = useState(false);
    const [isLoadingImage, setIsLoadingImage] = useState(false);

    useEffect(() => {
        fetch("http://localhost:8000/most_viral_tweets?limit=3")
            .then((res) => res.json())
            .then((data) => setTweets(data));
    }, []);

    const generateTweet = () => {
        setIsLoadingTweet(true);
        fetch("http://localhost:8000/generate_tweet", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: "Generate viral tweet" }),
        })
            .then((res) => res.json())
            .then((data) => setGeneratedTweet(data.tweet))
            .finally(() => setIsLoadingTweet(false));
    };

    const generateImage = () => {
        setIsLoadingImage(true);
        fetch("http://localhost:8000/generate_image", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: "Generate image" }),
        })
            .then((res) => res.json())
            .then((data) => setImage(data.image))
            .finally(() => setIsLoadingImage(false));
    };

    return (
        <div className="p-4 max-w-3xl mx-auto">
            <h1 className="text-2xl font-bold mb-6 text-center">Meme Boost Agent</h1>

            {/* Заголовок колонок */}
            <div className="flex items-center bg-gray-100 p-2 rounded-lg mb-2">
                <div className="w-24 text-center text-gray-700 font-bold">
                    Retweet Ratio (Higher is better)
                </div>
                <div className="flex-1 text-gray-700 font-bold ml-4">
                    Viral Tweets
                </div>
            </div>

            {/* Список виральных твитов */}
            <div className="space-y-4">
                {tweets.map((tweet, idx) => (
                    <div
                        key={idx}
                        className="border rounded-lg p-4 flex items-center bg-white shadow-sm"
                    >
                        {/* Ретвит ретио */}
                        <div className="w-24 text-center text-gray-500 font-semibold">
                            {Number(tweet.retweet_ratio).toFixed(2)}
                        </div>
                        {/* Текст твита */}
                        <div className="flex-1 text-gray-800 ml-4">
                            {tweet.text}
                        </div>
                    </div>
                ))}
            </div>

            {/* Кнопки для генерации */}
            <div className="mt-8 flex flex-col space-y-4">
                <div className="flex space-x-4">
                    <button
                        onClick={generateTweet}
                        className={`flex-1 p-3 rounded-lg ${isLoadingTweet ? "bg-gray-400 cursor-not-allowed" : "bg-green-500 hover:bg-green-600"
                            } text-white`}
                        disabled={isLoadingTweet}
                    >
                        {isLoadingTweet ? "Loading..." : "Generate Tweet"}
                    </button>
                    <button
                        onClick={generateImage}
                        className={`flex-1 p-3 rounded-lg ${isLoadingImage ? "bg-gray-400 cursor-not-allowed" : "bg-blue-500 hover:bg-blue-600"
                            } text-white`}
                        disabled={isLoadingImage}
                    >
                        {isLoadingImage ? "Loading..." : "Generate Image"}
                    </button>
                </div>

                {/* Отображение сгенерированного твита */}
                {generatedTweet && (
                    <div className="border rounded-lg p-4 bg-white shadow-sm">
                        <h2 className="text-lg font-semibold mb-2">Generated Tweet</h2>
                        <p className="text-gray-800">{generatedTweet}</p>
                    </div>
                )}

                {/* Отображение сгенерированного изображения */}
                {image && (
                    <div className="border rounded-lg p-4 bg-white shadow-sm">
                        <h2 className="text-lg font-semibold mb-2">Generated Image</h2>
                        <img src={`data:image/png;base64,${image}`} alt="Generated" className="w-full h-auto rounded-md" />
                    </div>
                )}
            </div>
        </div>
    );
}

export default TweetsPage;

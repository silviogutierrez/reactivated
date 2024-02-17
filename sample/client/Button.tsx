import React from "react";

export const Button = () => {
    const [count, setCount] = React.useState(0);

    return (
        <div>
            I am a 12 button {count} <br />
            <button onClick={() => setCount((count) => count + 1)}>Increase</button>
        </div>
    );
};

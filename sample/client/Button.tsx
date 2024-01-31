import React from "react";

export const Button = () => {
    const [count, setCount] = React.useState(0);

    return <div>I am a button {count} <br /><button onClick={() => setCount(count => count+1)}>Increase</button></div>;
}

import React from "react";
import {style} from "typestyle";
import Context from "reactivated/context";

import {AjaxPlayground} from "@client/generated";

export default class extends AjaxPlayground {
    static contextType = Context;

    handleOnClick = (event: React.FormEvent<HTMLButtonElement>) => {
        const url = new URL(this.context.request.url);
        fetch(url.toString(), {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
            body: JSON.stringify({thing: "I am post data"}),
        })
            .then(response => response.json())
            .then(({results}) => {
                console.log(results);
            });
    };

    render() {
        return (
            <div>
                <button onClick={this.handleOnClick}>Click me</button>
            </div>
        );
    }
}

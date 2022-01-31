import React from "react";

import {Types, Iterator, CSRFToken, reverse} from "@client/generated";
import {Layout} from "@client/components/Layout";

import {Widget} from "reactivated/forms";

export default ({question}: Types["ResultsProps"]) => (
    <Layout title={question.question_text}>
        <h1>{question.question_text}</h1>
        <ul>
            {question.choices.map((choice) => (
                <li key={choice.id}>
                    {choice.choice_text} -- {choice.votes} vote(s)
                </li>
            ))}
        </ul>

        <a href={reverse("poll_detail", {question_id: question.id})}>Vote again?</a>
    </Layout>
);

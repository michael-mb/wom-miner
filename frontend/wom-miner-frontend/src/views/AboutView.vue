<template>
    <div class="main-wrapper" id="main-wrapper">
        <Header/>
        <div class="page-wrapper">
            <div class="content container-fluid">
                <div class="page-header">
                    <div class="row">
                        <div class="col-sm-12">
                            <h3 class="page-title">About Page</h3>
                            <ul class="breadcrumb">
                                <li class="breadcrumb-item"><RouterLink to="/">Dashboard</RouterLink></li>
                                <li class="breadcrumb-item active">About Page</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-header">
                                <h4 class="card-title"><i class="fab fa-wpexplorer fs-30"></i> UNI - Explorer</h4>
                                <br>
                                <span class="sub-title ">Tutors:</span>
                                <span class="m-2">
                                    <router-link to="/detail/people-ude/vwLut4kBVxEu2HInbb8t">Dr. Marcus Handte, </router-link>
                                    <router-link to="/detail/people-ude/igLut4kBVxEu2HIng8AV">Arman Arzani</router-link>
                                </span>
                            </div>
                            <div class="card-body">
                                <p>The goal of this project group is to design and implement a web-based tool
                                    that supports the advisors and coaches of a university in identifying
                                    research groups or researchers that are working on innovative topics.
                                    As primary input the tool shall process the web pages of a university to
                                    automatically extract relevant information. Some examples for this are:</p>
                                <ul>
                                    <li> - The organization and structure of the university (names of the faculties,
                                        research groups and researchers, etc.)
                                    </li>
                                    <li> - The research projects of the different research groups
                                        (project name and topic, project duration, funding scheme and budget, etc.)
                                    </li>
                                </ul>
                                <br>
                                <p>The algorithms implemented as part of the tool shall be generic to support
                                    the data extraction from the web sites of different universities.
                                    To visualize the data, we develop this web-based application that enables
                                    business advisors and innovation coaches to browse and search the extracted information.
                                </p>
                                <p>
                                    On a technical level, web scraping and natural language processing (NLP) methods were used.
                                    Automated web scraping was used to crawl almost all of the university's web pages.
                                    Named Entity Recognition was used to identify persons and institutions.
                                    Keyword Extraction and Text Summarization with large language models were used to
                                    extract the content of the pages. Different rule-based methods were used to
                                    identify entities such as projects, chairs or faculties and their connections
                                    to each other.
                                </p>
                                <br>
                                <p>More information about the project on
                                    <router-link to="/detail/research_project-ude/research_miner_ude_89a908512399522035e8028e571b3722f3b1278e23b3c344aa3b0e7bcd8acd96">
                                        WOM - Web Organization Mining
                                    </router-link>
                                </p>
                                <br>
                                <p>
                                    <span style="font-size: 15px; font-weight: 500">Development team:</span> Lukas Glaser, Dennis Hilmer, Yelle Lieder,
                                    Theodor Vogl, Michael Mboni
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import Header from "@/components/Header.vue";
</script>
<style scoped>
.sub-title{
    font-size: 18px;
    font-weight: 500;
}
</style>